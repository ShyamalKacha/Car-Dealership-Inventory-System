import { useEffect, useState, type FormEvent } from "react";
import { useVehicles } from "../hooks/useVehicles";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import type { VehicleCategory } from "../types";

const CATEGORIES: VehicleCategory[] = [
  "SUV",
  "SEDAN",
  "TRUCK",
  "COUPE",
  "HATCHBACK",
  "VAN",
];

export function Dashboard() {
  const { vehicles, loading, error, fetchVehicles, searchVehicles, purchaseVehicle } =
    useVehicles();

  // Search form state
  const [make, setMake] = useState("");
  const [model, setModel] = useState("");
  const [category, setCategory] = useState("");
  const [priceMin, setPriceMin] = useState("");
  const [priceMax, setPriceMax] = useState("");
  const [purchasing, setPurchasing] = useState<number | null>(null);
  const [successMsg, setSuccessMsg] = useState("");

  useEffect(() => {
    fetchVehicles();
  }, [fetchVehicles]);

  const handleSearch = (e: FormEvent) => {
    e.preventDefault();
    searchVehicles({
      make: make || undefined,
      model: model || undefined,
      category: (category as VehicleCategory) || undefined,
      price_min: priceMin ? Number(priceMin) : undefined,
      price_max: priceMax ? Number(priceMax) : undefined,
    });
  };

  const handleClear = () => {
    setMake("");
    setModel("");
    setCategory("");
    setPriceMin("");
    setPriceMax("");
    fetchVehicles();
  };

  const handlePurchase = async (vehicleId: number) => {
    setPurchasing(vehicleId);
    setSuccessMsg("");
    try {
      await purchaseVehicle(vehicleId);
      setSuccessMsg("Purchase successful!");
      setTimeout(() => setSuccessMsg(""), 3000);
    } catch (err: any) {
      alert(err.response?.data?.detail || "Purchase failed");
    } finally {
      setPurchasing(null);
    }
  };

  return (
    <div>
      {/* Success toast */}
      {successMsg && (
        <div className="mb-4 rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 p-3 text-sm text-green-700 dark:text-green-300">
          {successMsg}
        </div>
      )}

      {/* Search / Filter bar */}
      <Card className="mb-6">
        <form onSubmit={handleSearch} className="flex flex-wrap gap-3 items-end">
          <div className="flex flex-col gap-1">
            <label className="text-xs font-medium text-[var(--color-text-secondary)]">Make</label>
            <input
              className="rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-primary)] px-3 py-2 text-sm w-32 focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]"
              placeholder="e.g. Toyota"
              value={make}
              onChange={(e) => setMake(e.target.value)}
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs font-medium text-[var(--color-text-secondary)]">Model</label>
            <input
              className="rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-primary)] px-3 py-2 text-sm w-32 focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]"
              placeholder="e.g. Camry"
              value={model}
              onChange={(e) => setModel(e.target.value)}
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs font-medium text-[var(--color-text-secondary)]">Category</label>
            <select
              className="rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-primary)] px-3 py-2 text-sm w-32 focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
            >
              <option value="">All</option>
              {CATEGORIES.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs font-medium text-[var(--color-text-secondary)]">Min Price</label>
            <input
              className="rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-primary)] px-3 py-2 text-sm w-28 focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]"
              type="number"
              min={0}
              placeholder="$0"
              value={priceMin}
              onChange={(e) => setPriceMin(e.target.value)}
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs font-medium text-[var(--color-text-secondary)]">Max Price</label>
            <input
              className="rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-primary)] px-3 py-2 text-sm w-28 focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]"
              type="number"
              min={0}
              placeholder="$99999"
              value={priceMax}
              onChange={(e) => setPriceMax(e.target.value)}
            />
          </div>
          <div className="flex gap-2">
            <Button type="submit" variant="primary">Search</Button>
            <Button type="button" variant="secondary" onClick={handleClear}>Clear</Button>
          </div>
        </form>
      </Card>

      {/* Error */}
      {error && (
        <div className="mb-4 rounded-lg border border-[var(--color-danger)]/30 bg-[var(--color-danger)]/5 p-3 text-sm text-[var(--color-danger)]">
          {error}
          <button className="ml-2 underline" onClick={handleClear}>Retry</button>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="flex justify-center py-20">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-[var(--color-border)] border-t-[var(--color-accent)]" />
        </div>
      )}

      {/* Empty */}
      {!loading && !error && vehicles.length === 0 && (
        <div className="flex flex-col items-center py-20 text-[var(--color-text-secondary)]">
          <p className="text-lg">No vehicles found</p>
          <p className="mt-1 text-sm">Try adjusting your search filters</p>
        </div>
      )}

      {/* Vehicle grid */}
      {!loading && !error && vehicles.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {vehicles.map((v) => (
            <Card key={v.id} className="flex flex-col">
              {/* Category badge */}
              <div className="mb-3">
                <span className="inline-block rounded-full bg-[var(--color-accent)]/10 px-2.5 py-0.5 text-xs font-medium text-[var(--color-accent)]">
                  {v.category}
                </span>
              </div>

              {/* Details */}
              <h3 className="text-lg font-semibold">
                {v.make} {v.model}
              </h3>
              <p className="mt-1 text-2xl font-bold text-[var(--color-accent)]">
                ${Number(v.price).toLocaleString()}
              </p>
              <div className="mt-auto pt-4 flex items-center justify-between">
                <span className={`text-sm font-medium ${
                  v.quantity > 0
                    ? "text-[var(--color-success)]"
                    : "text-[var(--color-danger)]"
                }`}>
                  {v.quantity > 0 ? `${v.quantity} in stock` : "Out of stock"}
                </span>
                <Button
                  variant="primary"
                  disabled={v.quantity === 0}
                  loading={purchasing === v.id}
                  onClick={() => handlePurchase(v.id)}
                >
                  Purchase
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
