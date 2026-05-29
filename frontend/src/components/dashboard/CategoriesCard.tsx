import { formatCurrency } from "@/lib/utils";

export interface CategoryComparison {
  category: string;
  current_amount: string;
  previous_amount: string;
  delta_percentage: string;
  severity: "good" | "warning" | "danger";
}

export function CategoriesCard({ categories }: { categories: CategoryComparison[] | null }) {
  if (!categories || categories.length === 0) {
    return (
      <section className="rounded-3xl border border-white/10 bg-white/5 p-6 shadow-2xl shadow-black/20 backdrop-blur">
        <p className="text-sm text-zinc-400">Categorias</p>
        <p className="mt-4 text-sm text-zinc-400">Sem dados de comparação.</p>
      </section>
    );
  }

  return (
    <section className="rounded-3xl border border-white/10 bg-white/5 p-6 shadow-2xl shadow-black/20 backdrop-blur">
      <p className="text-sm text-zinc-400">Categorias</p>

      <div className="mt-4 space-y-3">
        {categories.map((item) => (
          <article key={item.category} className="rounded-2xl border border-white/10 bg-black/20 p-4">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="font-medium text-zinc-50">{item.category}</p>
                <p className="mt-1 text-xs text-zinc-400">
                  Anterior: {formatCurrency(item.previous_amount)}
                </p>
              </div>
              <div className="text-right">
                <p className="text-lg font-semibold text-zinc-50">
                  {formatCurrency(item.current_amount)}
                </p>
                <p className="mt-1 text-xs text-zinc-400">{item.delta_percentage}%</p>
              </div>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}