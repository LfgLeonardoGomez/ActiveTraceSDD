import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import type { ComunicacionPorDocente } from '../../types/auditoria.types';

interface ComunicacionesChartProps {
  data: ComunicacionPorDocente[];
}

export default function ComunicacionesChart({ data }: ComunicacionesChartProps) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base">Comunicaciones por docente</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="docente_nombre" tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} allowDecimals={false} />
            <Tooltip />
            <Legend />
            <Bar dataKey="enviadas" stackId="a" fill="#22c55e" />
            <Bar dataKey="pendientes" stackId="a" fill="#f59e0b" />
            <Bar dataKey="fallidas" stackId="a" fill="#ef4444" />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
