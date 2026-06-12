import KPICard from '@/shared/components/KPICard';

interface KpiCardsProps {
  totalSinFactura: number;
  totalConFactura: number;
}

export default function KpiCards({ totalSinFactura, totalConFactura }: KpiCardsProps) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <KPICard title="Total sin factura" value={totalSinFactura} format="currency" />
      <KPICard title="Total con factura" value={totalConFactura} format="currency" />
      <KPICard
        title="Total general"
        value={totalSinFactura + totalConFactura}
        format="currency"
        delta={totalConFactura}
      />
    </div>
  );
}
