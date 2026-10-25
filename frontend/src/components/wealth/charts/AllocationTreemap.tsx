import { ResponsiveContainer, Treemap, Tooltip } from "recharts";
import { formatCurrency } from "@/lib/utils";

interface TreemapNode {
  name: string;
  size: number;
  fill: string;
  peso?: number; // Percentual na carteira (0-100)
  [key: string]: unknown;
}

interface AllocationTreemapProps {
  data: TreemapNode[];
}

interface CustomizedContentProps {
  x?: number;
  y?: number;
  width?: number;
  height?: number;
  name?: string;
  fill?: string;
  peso?: number;
}

const CustomizedContent = (props: CustomizedContentProps) => {
  const { x = 0, y = 0, width = 0, height = 0, name = "", fill = "", peso } = props;

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
            fill="#000000"
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
              fill="rgba(0,0,0,0.65)"
              fontSize={10}
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
                <div className="rounded-xl border border-border bg-popover p-3 text-popover-foreground shadow-xl">
                  <p className="mb-1 text-sm font-semibold">{node.name}</p>
                  <p className="text-xs text-muted-foreground">Valor: {formatCurrency(node.value)}</p>
                  {node.peso !== undefined && (
                    <p className="mt-0.5 text-xs text-muted-foreground">Peso: {node.peso.toFixed(1)}%</p>
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
