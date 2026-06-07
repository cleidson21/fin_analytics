from __future__ import annotations

import csv
import logging
from io import StringIO
from typing import Dict, Any, List
from datetime import datetime
from decimal import Decimal, InvalidOperation

logger = logging.getLogger(__name__)

class AmbiguousFileException(Exception):
    """Lançada quando a auto-detecção de CSV falha."""
    pass

class EmptyFileException(Exception):
    """Lançada quando o CSV está vazio."""
    pass


class MyProfitParser:
    def detect_type(self, raw_text: str) -> str:
        raw_text = raw_text.lstrip('\ufeff')
        if not raw_text or not raw_text.strip():
            raise EmptyFileException("O arquivo enviado está vazio.")
            
        lines = raw_text.strip().splitlines()
        if not lines:
            raise EmptyFileException("O arquivo enviado está vazio.")
            
        header = lines[0].lower()
        
        # Padrões de identificação de colunas comuns em cada tipo
        is_proventos = ("ativo" in header) and (("evento" in header and ("valor líquido" in header or "valor liquido" in header)) or ("recebido" in header and "data pgto." in header))
        is_posicoes = ("ativo" in header) and ("quantidade" in header or "qtd" in header) and ("preço médio" in header or "preco medio" in header or "preço de aquisição" in header)
        is_evolucao = ("patrimônio" in header or "patrimonio" in header) and ("rentabilidade" in header or "% mensal" in header)
        
        if is_proventos:
            return "PROVENTOS"
        elif is_posicoes:
            return "POSICOES"
        elif is_evolucao:
            return "EVOLUCAO"
        else:
            raise AmbiguousFileException("Não foi possível inferir o tipo do arquivo pelo cabeçalho.")

    def parse_preview(self, raw_text: str, file_type: str | None = None) -> Dict[str, Any]:
        """Faz a leitura superficial do CSV apenas para levantar o Preview, sem gerar objetos completos."""
        raw_text = raw_text.lstrip('\ufeff')
        logger.info(f"raw_text recebido (1000 chars): {raw_text[:1000]}")
        
        if not raw_text or not raw_text.strip():
            raise EmptyFileException("O arquivo enviado está vazio.")

        if not file_type:
            file_type = self.detect_type(raw_text)

        reader = csv.DictReader(StringIO(raw_text.strip()), delimiter=';')
        
        # Caso o delimiter seja vírgula, fallback:
        if reader.fieldnames and len(reader.fieldnames) == 1 and "," in reader.fieldnames[0]:
            reader = csv.DictReader(StringIO(raw_text.strip()), delimiter=',')
            
        if not reader.fieldnames:
            raise AmbiguousFileException("O arquivo não possui cabeçalhos válidos.")

        total_rows = 0
        tickers_found = set()
        warnings_count = 0
        errors_count = 0
        dates = []
        parsed_items = []
        
        # Helper para conversões
        def parse_br_date(val: str) -> str | None:
            if not val: return None
            try:
                v = val.strip()
                if "-" in v and len(v.split("-")) == 2:
                    m_str, y_str = v.split("-")
                    m_map = {"jan":1,"fev":2,"mar":3,"abr":4,"mai":5,"jun":6,"jul":7,"ago":8,"set":9,"out":10,"nov":11,"dez":12}
                    m_int = m_map.get(m_str.lower())
                    if m_int:
                        return f"{y_str}-{m_int:02d}-01"
                        
                # Pode vir dd/mm/yyyy ou mm/yyyy
                if len(v) == 7: # mm/yyyy
                    dt = datetime.strptime(v, "%m/%Y")
                else:
                    dt = datetime.strptime(v, "%d/%m/%Y")
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                return None
                
        def parse_br_decimal(val: str) -> Decimal | None:
            if not val: return None
            v = val.replace("R$", "").replace("%", "").strip()
            if v == "" or v == "-": return Decimal("0")
            
            # Handle mixed formats
            if "." in v and "," in v:
                if v.rfind(".") > v.rfind(","):
                    # US format: 1,234.56 -> 1234.56
                    v = v.replace(",", "")
                else:
                    # BR format: 1.234,56 -> 1234.56
                    v = v.replace(".", "").replace(",", ".")
            elif "," in v:
                # Only comma: assume BR decimal (1234,56)
                v = v.replace(",", ".")
            elif "." in v:
                # Only dot: assume US decimal (1234.56) or BR thousands (1.234)
                # If there are exactly 3 digits after the dot, and it's the only dot, 
                # it's ambiguous but usually in finance it's a US decimal if there's no comma.
                # However, if it ends with .00 it's obviously decimal. 
                # We will leave the dot as is, so '55.20' remains '55.20'
                pass

            try:
                return Decimal(v)
            except InvalidOperation:
                return None

        for row_num, row in enumerate(reader, start=2): # +1 pra considerar o cabeçalho
            # Ignora linhas totalmente vazias silenciosamente
            if not any(row.values()):
                continue
                
            total_rows += 1
            item = {
                "source_line_no": row_num,
                "validation_status": "VALID",
                "validation_message": None
            }
            
            # Pega o Ativo (Ticket) se existir
            ativo = row.get("Ativo") or row.get("ativo") or row.get("Ticker") or row.get("ticker")
            if ativo:
                ativo = ativo.strip()
                tickers_found.add(ativo)
                item["ticker"] = ativo
            elif file_type in ("PROVENTOS", "POSICOES"):
                item["validation_status"] = "WARNING"
                item["validation_message"] = "Ticker ausente"
                warnings_count += 1
                
            # Extrai Data
            data_raw = None
            if file_type == "PROVENTOS":
                data_raw = row.get("Data Pagamento") or row.get("Data pgto.") or row.get("Data") or row.get("data")
            elif file_type == "EVOLUCAO":
                data_raw = row.get("Mês") or row.get("Mes") or row.get("mes") or row.get("Data") or row.get("data")
                
            if data_raw:
                dt_iso = parse_br_date(data_raw)
                if not dt_iso:
                    item["validation_status"] = "ERROR"
                    item["validation_message"] = f"Formato de data inválido: {data_raw}"
                    errors_count += 1
                else:
                    dates.append(dt_iso)
                    if file_type == "PROVENTOS":
                        item["data_pagamento"] = dt_iso
                    elif file_type == "EVOLUCAO":
                        item["reference_month"] = dt_iso
            else:
                if file_type in ("PROVENTOS", "EVOLUCAO"):
                    item["validation_status"] = "ERROR"
                    item["validation_message"] = "Data obrigatória ausente"
                    errors_count += 1
            
            # Garante snapshot para POSICOES
            if file_type == "POSICOES" and not item.get("data_snapshot"):
                item["data_snapshot"] = datetime.today().strftime("%Y-%m-%d")
                    
            # Validar valores zerados ou inconsistentes
            if file_type == "PROVENTOS":
                v_liq_raw = row.get("Valor Líquido") or row.get("valor liquido") or row.get("Recebido")
                if not v_liq_raw:
                    if item["validation_status"] != "ERROR":
                        item["validation_status"] = "ERROR"
                        item["validation_message"] = "Valor ausente"
                        errors_count += 1
                else:
                    v_liq = parse_br_decimal(v_liq_raw)
                    if v_liq is None:
                        item["validation_status"] = "ERROR"
                        item["validation_message"] = "Valor corrompido"
                        errors_count += 1
                    else:
                        item["valor_liquido"] = float(v_liq)
                        item["valor_liquido_cents"] = int(v_liq * 100)
                        if v_liq == Decimal("0") and item["validation_status"] == "VALID":
                            item["validation_status"] = "WARNING"
                            item["validation_message"] = "Valor zerado"
                            warnings_count += 1
                
                # Outros campos úteis pro staging proventos
                item["tipo_evento"] = row.get("Categoria") or row.get("Tipo") or "DIVIDENDO"
                        
            elif file_type == "POSICOES":
                qtde_raw = row.get("Quantidade") or row.get("quantidade") or row.get("Qtd")
                if qtde_raw:
                    qtde = parse_br_decimal(qtde_raw)
                    if qtde is None:
                        item["validation_status"] = "ERROR"
                        item["validation_message"] = "Qtde corrompida"
                        errors_count += 1
                    else:
                        item["quantidade"] = float(qtde)
                        if qtde == Decimal("0") and item["validation_status"] == "VALID":
                            item["validation_status"] = "WARNING"
                            item["validation_message"] = "Posição zerada"
                            warnings_count += 1
                            
                item["preco_medio"] = float(parse_br_decimal(row.get("Preço Médio") or "0") or 0)
                item["total_investido"] = float(parse_br_decimal(row.get("Custo Total") or row.get("Total investido") or "0") or 0)
                item["preco_atual"] = float(parse_br_decimal(row.get("Cotação Atual") or row.get("Preço atual") or "0") or 0)
                item["total_atual"] = float(parse_br_decimal(row.get("Valor Atual") or row.get("Total atual") or "0") or 0)
                item["ganho"] = float(parse_br_decimal(row.get("Lucro/Prejuízo") or row.get("Ganho") or "0") or 0)
                
            elif file_type == "EVOLUCAO":
                item["rentabilidade_mensal_pct"] = float(parse_br_decimal(row.get("Rentabilidade do Mês (%)") or row.get("% Mensal") or "0") or 0)
                item["rentabilidade_acumulada_pct"] = float(parse_br_decimal(row.get("Rentabilidade Acumulada (%)") or row.get("% Acumulada") or "0") or 0)
                item["patrimonio_cents"] = int((parse_br_decimal(row.get("Patrimônio (R$)") or row.get("Patrimônio") or "0") or Decimal(0)) * 100)
                item["compras_cents"] = int((parse_br_decimal(row.get("Total de Compras (R$)") or row.get("Compras") or "0") or Decimal(0)) * 100)
                item["vendas_cents"] = int((parse_br_decimal(row.get("Total de Vendas (R$)") or row.get("Vendas") or "0") or Decimal(0)) * 100)
                item["proventos_cents"] = int((parse_br_decimal(row.get("Dividendos e JCP Recebidos no Mês (R$)") or row.get("Proventos") or "0") or Decimal(0)) * 100)
                
                # Novos índices do arquivo MyProfit (se existirem)
                item["ibov_mensal_pct"] = float(parse_br_decimal(row.get("IBOV Mensal") or "0") or 0)
                item["ibov_acumulado_pct"] = float(parse_br_decimal(row.get("IBOV Acumulado") or "0") or 0)
                item["cdi_mensal_pct"] = float(parse_br_decimal(row.get("CDI Mensal") or "0") or 0)
                item["cdi_acumulado_pct"] = float(parse_br_decimal(row.get("CDI Acumulado") or "0") or 0)
                item["ipca_mensal_pct"] = float(parse_br_decimal(row.get("IPCA Mensal") or "0") or 0)
                item["ipca_acumulado_pct"] = float(parse_br_decimal(row.get("IPCA Acumulado") or "0") or 0)
                item["ifix_mensal_pct"] = float(parse_br_decimal(row.get("IFIX Mensal") or "0") or 0)
                item["ifix_acumulado_pct"] = float(parse_br_decimal(row.get("IFIX Acumulado") or "0") or 0)
                item["sp500_mensal_pct"] = float(parse_br_decimal(row.get("S&P Mensal") or "0") or 0)
                item["sp500_acumulado_pct"] = float(parse_br_decimal(row.get("S&P Acumulado") or "0") or 0)
                item["idiv_mensal_pct"] = float(parse_br_decimal(row.get("IDIV Mensal") or "0") or 0)
                item["idiv_acumulado_pct"] = float(parse_br_decimal(row.get("IDIV Acumulado") or "0") or 0)
            
            parsed_items.append(item)
            
        dates.sort()
        period_start = dates[0] if dates else None
        period_end = dates[-1] if dates else None

        return {
            "source_type": "MYPROFIT",
            "file_type": file_type,
            "tickers_found": list(tickers_found),
            "total_rows": total_rows,
            "period_start": period_start,
            "period_end": period_end,
            "warnings": warnings_count,
            "errors": errors_count,
            "parsed_items": parsed_items
        }
