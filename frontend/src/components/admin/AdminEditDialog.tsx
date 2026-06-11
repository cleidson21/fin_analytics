import React from "react";
import { X } from "lucide-react";

interface AdminEditDialogProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
}

export function AdminEditDialog({ isOpen, onClose, title, children }: AdminEditDialogProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="w-full max-w-lg rounded-md border border-zinc-800 bg-zinc-950 shadow-lg sm:max-w-[425px]">
        <div className="flex items-center justify-between border-b border-zinc-800 px-4 py-3">
          <h2 className="text-lg font-semibold text-zinc-100">{title}</h2>
          <button
            onClick={onClose}
            className="rounded-sm opacity-70 ring-offset-zinc-950 transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-zinc-800 focus:ring-offset-2"
          >
            <X className="h-4 w-4 text-zinc-400" />
            <span className="sr-only">Fechar</span>
          </button>
        </div>
        <div className="p-4">{children}</div>
      </div>
    </div>
  );
}
