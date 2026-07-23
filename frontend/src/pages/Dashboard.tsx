import { useEffect, useState, type FormEvent } from "react";
import { useVehicles } from "../hooks/useVehicles";
import { useAuth } from "../context/AuthContext";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import type { VehicleCategory } from "../types";

const CATEGORIES: VehicleCategory[] = [
  "SUV", "SEDAN", "TRUCK", "COUPE", "HATCHBACK", "VAN",
];

function SkeletonCard() {
  return (
    <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-card)] p-6 shadow-sm">
      <div className="mb-3 h-5 w-16 rounded-full bg-[var(--color-border)] animate-pulse" />
      <div className="mb-1 h-6 w-3/4 rounded bg-[var(--color-border)] animate-pulse" />
      <div className="mt-1 h-7 w-1/2 rounded bg-[var(--color-border)] animate-pulse" />
      <div className="mt-4 flex items-center justify-between">
        <div className="h-4 w-20 rounded bg-[var(--color-border)] animate-pulse" />
        <div className="h-9 w-24 rounded-lg bg-[var(--color-border)] animate-pulse" />
      </div>
    </div>
  );
}

export function Dashboard() {
  const { vehicles, loading, error, fetchVehicles, searchVehicles, purchaseVehicle } = useVehicles();
  const { user } = useAuth();

  const [make, setMake] = useState("");
  const [model, setModel] = useState("");
  const [category, setCategory] = useState("");
  const [priceMin, setPriceMin] = useState("");
  const [priceMax, setPriceMax] = useState("");
  const [purchasing, setPurchasing] = useState<number | null>(null);
  const [toast, setToast] = useState<{ type: "success" | "error"; message: string } | null>(null);

  useEffect(() => {
    fetchVehicles();
  }, [fetchVehicles]);

  useEffect(() => {
    if (toast) {
      const t = setTimeout(() => setToast(null), 3000);
      return () => clearTimeout(t);
    }
  }, [toast]);

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
    setMake(""); setModel(""); setCategory(""); setPriceMin(""); setPriceMax("");
    fetchVehicles();
  };

  const handlePurchase = async (vehicleId: number) => {
    setPurchasing(vehicleId);
    try {
      await purchaseVehicle(vehicleId);
      setToast({ type: "success", message: "Purchase successful!" });
    } catch (err: any) {
      setToast({ type: "error", message: err.response?.data?.detail || "Purchase failed" });
    } finally {
      setPurchasing(null);
    }
  };

  return (
    <div>
      {/* Toast */}
      {toast && (
        <div className={`fixed top-20 right-4 z-50 animate-slide-down rounded-lg border px-4 py-3 text-sm shadow-lg ${
          toast.type === "success"
            ? "border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-300"
            : "border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-300"
        }`}>
          <div className="flex items-center gap-2">
            {toast.type === "success" ? (
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
              </svg>
            ) : (
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            )}
            {toast.message}
          </div>
        </div>
      )}

      {/* Hero */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold">Vehicle Inventory</h1>
        <p className="mt-1 text-[var(--color-text-secondary)]">
          Browse, search, and purchase from our available inventory
        </p>
      </div>

      {/* Search */}
      <Card className="mb-6" hover={false}>
        <form onSubmit={handleSearch} className="flex flex-wrap gap-3 items-end">
          <div className="flex flex-col gap-1">
            <label className="text-sm font-medium text-[var(--color-text-secondary)]">Make</label>
            <input
              className="rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-primary)] px-3 py-2 text-sm w-32 focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)] transition-shadow"
              placeholder="Toyota"
              value={make}
              onChange={(e) => setMake(e.target.value)}
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-sm font-medium text-[var(--color-text-secondary)]">Model</label>
            <input
              className="rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-primary)] px-3 py-2 text-sm w-32 focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)] transition-shadow"
              placeholder="Camry"
              value={model}
              onChange={(e) => setModel(e.target.value)}
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-sm font-medium text-[var(--color-text-secondary)]">Category</label>
            <select
              className="rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-primary)] px-3 py-2 text-sm w-32 focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
            >
              <option value="">All</option>
              {CATEGORIES.map((c) => (<option key={c} value={c}>{c}</option>))}
            </select>
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-sm font-medium text-[var(--color-text-secondary)]">Min Price</label>
            <input
              className="rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-primary)] px-3 py-2 text-sm w-28 focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)] transition-shadow"
              type="number" min={0} placeholder="₹0"
              value={priceMin}
              onChange={(e) => setPriceMin(e.target.value)}
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-sm font-medium text-[var(--color-text-secondary)]">Max Price</label>
            <input
              className="rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-primary)] px-3 py-2 text-sm w-28 focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)] transition-shadow"
              type="number" min={0} placeholder="₹99999"
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
        <div className="mb-6 rounded-lg border border-[var(--color-danger)]/30 bg-[var(--color-danger-light)] px-4 py-3 text-sm text-[var(--color-danger)] animate-slide-up">
          {error}
          <button className="ml-2 underline font-medium" onClick={handleClear}>Retry</button>
        </div>
      )}

      {/* Skeleton loading */}
      {loading && (
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      )}

      {/* Empty */}
      {!loading && !error && vehicles.length === 0 && (
        <div className="flex flex-col items-center py-20 text-[var(--color-text-secondary)] animate-fade-in">
          <svg className="w-16 h-16 mb-4 opacity-30" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
          </svg>
          <p className="text-lg font-medium">No vehicles found</p>
          <p className="mt-1 text-sm">Try adjusting your search filters</p>
        </div>
      )}

      {/* Vehicle grid */}
      {!loading && !error && vehicles.length > 0 && (
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {vehicles.map((v) => (
            <Card key={v.id} className="flex flex-col group cursor-default">
              {/* Category badge */}
              <div className="mb-3">
                <span className="inline-block rounded-full bg-[var(--color-accent-light)] px-2.5 py-0.5 text-xs font-medium text-[var(--color-accent)]">
                  {v.category}
                </span>
              </div>

              <h3 className="text-lg font-semibold group-hover:text-[var(--color-accent)] transition-colors">
                {v.make} {v.model}
              </h3>
              <p className="mt-1 text-2xl font-bold text-[var(--color-accent)]">
              ₹{Number(v.price).toLocaleString("en-IN")}
              </p>

              <div className="mt-auto pt-4 flex items-center justify-between">
                <span className={`text-sm font-medium ${
                  v.quantity > 0
                    ? "text-[var(--color-success)]"
                    : "text-[var(--color-danger)]"
                }`}>
                  {v.quantity > 0 ? `${v.quantity} in stock` : "Out of stock"}
                </span>
                {user?.role !== "admin" && (
                  <Button
                    variant="primary"
                    disabled={v.quantity === 0}
                    loading={purchasing === v.id}
                    onClick={() => handlePurchase(v.id)}
                  >
                    Purchase
                  </Button>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
