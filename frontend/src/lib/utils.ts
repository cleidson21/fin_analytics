import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatCurrency(value: string | number) {
  return Number(value).toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  });
}

export function colorForValue(value: number, invertido = false): string {
  if (invertido) return value > 0 ? "text-[#e97070]" : "text-[#4ecf98]";
  return value > 0 ? "text-[#4ecf98]" : "text-[#e97070]";
}

export function getScoreColor(score: number): string {
  if (score >= 66) return "text-[#4ecf98]";
  if (score >= 41) return "text-[#f5a623]";
  return "text-[#e97070]";
}
