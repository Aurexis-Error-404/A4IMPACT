type Props = {
  groups: string[];
  selectedGroup: string;
  onChange: (value: string) => void;
};

export function CommodityGroupSelector({
  groups,
  selectedGroup,
  onChange,
}: Props) {
  return (
    <div className="filter-card">
      <label htmlFor="commodity-group">Crop type</label>
      <select
        id="commodity-group"
        value={selectedGroup}
        onChange={(event) => onChange(event.target.value)}
      >
        {groups.map((group) => (
          <option key={group} value={group}>
            {group}
          </option>
        ))}
      </select>
    </div>
  );
}
