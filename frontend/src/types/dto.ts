export interface PaginatedResponse<T> {
  items: T[];
  total: number;
}

export interface UpdateTransactionDTO {
  categoria: string;
  macro_categoria: string;
  parcelamento: string;
  observacao: string;
}

export interface UpdatePositionDTO {
  classe_ativo: string;
  observacao: string;
}

export interface UpdateDividendDTO {
  ticker: string;
  tipo_evento: string;
  observacao: string;
}

