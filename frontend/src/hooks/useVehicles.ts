import { useState, useCallback } from "react";
import api from "../api/client";
import type { Vehicle, VehicleCategory } from "../types";

interface SearchParams {
  make?: string;
  model?: string;
  category?: VehicleCategory;
  price_min?: number;
  price_max?: number;
}

export function useVehicles() {
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchVehicles = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get("/api/vehicles");
      setVehicles(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to load vehicles");
    } finally {
      setLoading(false);
    }
  }, []);

  const searchVehicles = useCallback(async (params: SearchParams) => {
    setLoading(true);
    setError(null);
    try {
      const query = new URLSearchParams();
      if (params.make) query.set("make", params.make);
      if (params.model) query.set("model", params.model);
      if (params.category) query.set("category", params.category);
      if (params.price_min !== undefined) query.set("price_min", String(params.price_min));
      if (params.price_max !== undefined) query.set("price_max", String(params.price_max));
      const res = await api.get(`/api/vehicles/search?${query.toString()}`);
      setVehicles(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Search failed");
    } finally {
      setLoading(false);
    }
  }, []);

  const purchaseVehicle = useCallback(async (vehicleId: number) => {
    const res = await api.post(`/api/vehicles/${vehicleId}/purchase`);
    // Update the specific vehicle in state
    setVehicles((prev) =>
      prev.map((v) => (v.id === vehicleId ? res.data : v))
    );
    return res.data as Vehicle;
  }, []);

  return { vehicles, loading, error, fetchVehicles, searchVehicles, purchaseVehicle };
}
