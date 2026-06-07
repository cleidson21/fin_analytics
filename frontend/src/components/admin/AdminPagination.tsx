import React from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";

interface AdminPaginationProps {
  total: number;
  limit: number;
  offset: number;
  onPageChange: (newOffset: number) => void;
}

export function AdminPagination({
  total,
  limit,
  offset,
  onPageChange,
}: AdminPaginationProps) {
  const currentPage = Math.floor(offset / limit) + 1;
  const totalPages = Math.max(1, Math.ceil(total / limit));

  const handlePrev = () => {
    if (offset >= limit) {
      onPageChange(offset - limit);
    }
  };

  const handleNext = () => {
    if (offset + limit < total) {
      onPageChange(offset + limit);
    }
  };

  return (
    <div className="flex items-center justify-between px-2 py-4">
      <div className="text-sm text-zinc-400">
        Mostrando{" "}
        <span className="font-medium text-zinc-200">
          {total === 0 ? 0 : offset + 1}
        </span>{" "}
        a{" "}
        <span className="font-medium text-zinc-200">
          {Math.min(offset + limit, total)}
        </span>{" "}
        de <span className="font-medium text-zinc-200">{total}</span>{" "}
        registros
      </div>
      <div className="flex items-center space-x-6 lg:space-x-8">
        <div className="flex items-center space-x-2">
          <Button
            variant="admin-outline"
            className="h-8 w-8 p-0"
            onClick={handlePrev}
            disabled={currentPage === 1}
          >
            <ChevronLeft className="h-4 w-4" />
            <span className="sr-only">Página anterior</span>
          </Button>
          <div className="flex items-center justify-center text-sm font-medium text-zinc-300">
            Página {currentPage} de {totalPages || 1}
          </div>
          <Button
            variant="admin-outline"
            className="h-8 w-8 p-0"
            onClick={handleNext}
            disabled={currentPage >= totalPages}
          >
            <ChevronRight className="h-4 w-4" />
            <span className="sr-only">Próxima página</span>
          </Button>
        </div>
      </div>
    </div>
  );
}
