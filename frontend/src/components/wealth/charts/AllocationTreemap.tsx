import { ResponsiveContainer, Treemap, Tooltip } from "recharts";
import { formatCurrency } from "@/lib/utils";

interface TreemapNode {
  name: string;
  size: number;
  fill: string;
  peso?: number; // Percentual na carteira (0-100)
  [key: string]: any;
}

interface AllocationTreemapProps {
  data: TreemapNode[];
}

const CustomizedContent = (props: any) => {
  const { root, depth, x, y, width, height, index, name, value, fill, peso } = props;

  // Se a caixa for muito pequena, não renderiza texto
  const showText = width > 50 && height > 35;
  
  // Truncar textos muito longos com base na largura disponível (aprox. 7 pixels por caractere)
  const maxChars = Math.max(3, Math.floor(width / 7.5));
  const displayName = name.length > maxChars ? name.substring(0, maxChars - 2) + ".." : name;

  return (
    <g>
      <rect
        x={x}
        y={y}
        width={width}
        height={height}
        fill={fill}
        stroke="#1a1a1a"
        strokeWidth={2}
        className="cursor-pointer hover:brightness-110 transition-all duration-200"
      />
      {showText && (
        <>
          <text
            x={x + width / 2}
            y={y + height / 2 - (peso && height > 45 ? 6 : 0)}
            textAnchor="middle"
            fill="#ffffff"
            fontSize={Math.min(13, height / 3)} 
            fontWeight={600}
            className="pointer-events-none select-none"
          >
            {displayName}
          </text>
          {peso !== undefined && height > 45 && (
            <text
              x={x + width / 2}
              y={y + height / 2 + 10}
              textAnchor="middle"
              fill="rgba(255,255,255,0.85)"
              fontSize={10} // Fixo e pequeno
              className="pointer-events-none select-none"
            >
              {peso.toFixed(1)}%
            </text>
          )}
        </>
      )}
    </g>
  );
};

export function AllocationTreemap({ data }: AllocationTreemapProps) {
  if (!data || data.length === 0) return null;

  return (
    <ResponsiveContainer width="100%" height="100%" minWidth={1} minHeight={1}>
      <Treemap
        data={data}
        dataKey="size"
        aspectRatio={4 / 3}
        stroke="#1a1a1a"
        fill="#8884d8"
        content={<CustomizedContent />}
      >
        <Tooltip 
          content={({ payload }) => {
            if (payload && payload.length > 0) {
              const node = payload[0].payload;
              return (
                <div className="bg-[#242424] border border-white/[0.08] rounded-xl p-3 text-white shadow-xl">
                  <p className="font-semibold text-sm mb-1">{node.name}</p>
                  <p className="text-xs text-neutral-400">Valor: {formatCurrency(node.value)}</p>
                  {node.peso !== undefined && (
                    <p className="text-xs text-neutral-500 mt-0.5">Peso: {node.peso.toFixed(1)}%</p>
                  )}
                </div>
              );
            }
            return null;
          }}
        />
      </Treemap>
    </ResponsiveContainer>
  );
}
