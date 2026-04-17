type Props = {
  commodities: string[];
  selectedCommodity: string;
  onChange: (value: string) => void;
};

export function CommoditySelector({
  commodities,
  selectedCommodity,
  onChange,
}: Props) {
  return (
    <div className="filter-card">
      <label htmlFor="commodity">Commodity</label>
      <select
        id="commodity"
        value={selectedCommodity}
        onChange={(event) => onChange(event.target.value)}
      >
        {commodities.map((commodity) => (
          <option key={commodity} value={commodity}>
            {commodity}
          </option>
        ))}
      </select>
    </div>
  );
}
