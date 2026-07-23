import { useEffect, useState, type FormEvent } from "react";
import { useVehicles } from "../hooks/useVehicles";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { Card } from "../components/ui/Card";
import { Modal } from "../components/ui/Modal";
import api from "../api/client";
import type { Vehicle, VehicleCategory } from "../types";

const CATEGORIES: VehicleCategory[] = [
  "SUV", "SEDAN", "TRUCK", "COUPE", "HATCHBACK", "VAN",
];

interface FormData {
  make: string; model: string; category: VehicleCategory; price: string; quantity: string;
}

const emptyForm: FormData = { make: "", model: "", category: "SEDAN", price: "", quantity: "" };

export function Admin() {
  const { vehicles, loading, error, fetchVehicles, searchVehicles } = useVehicles();

  // Search
  const [searchMake, setSearchMake] = useState("");
  const [searchModel, setSearchModel] = useState("");
  const [searchCategory, setSearchCategory] = useState("");

  // Modals
  const [addOpen, setAddOpen] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [editId, setEditId] = useState<number | null>(null);
  const [restockId, setRestockId] = useState<number | null>(null);
  const [restockQty, setRestockQty] = useState("1");
  const [deleteId, setDeleteId] = useState<number | null>(null);
  const [form, setForm] = useState<FormData>(emptyForm);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState("");

  useEffect(() => { fetchVehicles(); }, [fetchVehicles]);

  // Search handler
  const handleSearch = (e: FormEvent) => {
    e.preventDefault();
    searchVehicles({
      make: searchMake || undefined,
      model: searchModel || undefined,
      category: (searchCategory as VehicleCategory) || undefined,
    });
  };

  const handleClear = () => {
    setSearchMake(""); setSearchModel(""); setSearchCategory("");
    fetchVehicles();
  };

  // CRUD
  const openAdd = () => { setForm(emptyForm); setFormError(""); setAddOpen(true); };

  const handleAdd = async (e: FormEvent) => {
    e.preventDefault();
    setFormError("");
    if (!form.make || !form.model || !form.price) { setFormError("Make, model, and price are required"); return; }
    setSubmitting(true);
    try {
      await api.post("/api/vehicles", {
        make: form.make, model: form.model, category: form.category,
        price: form.price, quantity: form.quantity ? Number(form.quantity) : 0,
      });
      setAddOpen(false); fetchVehicles();
    } catch (err: any) { setFormError(err.response?.data?.detail || "Failed to add vehicle"); }
    finally { setSubmitting(false); }
  };

  const openEdit = (v: Vehicle) => {
    setForm({ make: v.make, model: v.model, category: v.category, price: String(v.price), quantity: String(v.quantity) });
    setEditId(v.id); setFormError(""); setEditOpen(true);
  };

  const handleEdit = async (e: FormEvent) => {
    e.preventDefault();
    if (editId === null) return;
    setFormError(""); setSubmitting(true);
    try {
      await api.put(`/api/vehicles/${editId}`, {
        make: form.make || undefined, model: form.model || undefined,
        category: form.category || undefined, price: form.price ? Number(form.price) : undefined,
        quantity: form.quantity ? Number(form.quantity) : undefined,
      });
      setEditOpen(false); setEditId(null); fetchVehicles();
    } catch (err: any) { setFormError(err.response?.data?.detail || "Failed to update vehicle"); }
    finally { setSubmitting(false); }
  };

  const handleDelete = async () => {
    if (deleteId === null) return;
    try { await api.delete(`/api/vehicles/${deleteId}`); setDeleteId(null); fetchVehicles(); }
    catch (err: any) { alert(err.response?.data?.detail || "Failed to delete vehicle"); }
  };

  const handleRestock = async () => {
    if (restockId === null) return;
    const qty = Number(restockQty);
    if (!qty || qty < 1) return;
    try { await api.post(`/api/vehicles/${restockId}/restock`, { quantity: qty }); setRestockId(null); setRestockQty("1"); fetchVehicles(); }
    catch (err: any) { alert(err.response?.data?.detail || "Failed to restock"); }
  };

  return (
    <div className="animate-fade-in">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Admin Panel</h1>
          <p className="mt-1 text-sm text-[var(--color-text-secondary)]">Manage vehicle inventory</p>
        </div>
        <Button onClick={openAdd}>Add Vehicle</Button>
      </div>

      {/* Search bar */}
      <Card className="mb-6" hover={false}>
        <form onSubmit={handleSearch} className="flex flex-wrap gap-3 items-end">
          <div className="flex flex-col gap-1">
            <label className="text-sm font-medium text-[var(--color-text-secondary)]">Make</label>
            <input className="rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-primary)] px-3 py-2 text-sm w-32 focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]"
              placeholder="Toyota" value={searchMake} onChange={(e) => setSearchMake(e.target.value)} />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-sm font-medium text-[var(--color-text-secondary)]">Model</label>
            <input className="rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-primary)] px-3 py-2 text-sm w-32 focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]"
              placeholder="Camry" value={searchModel} onChange={(e) => setSearchModel(e.target.value)} />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-sm font-medium text-[var(--color-text-secondary)]">Category</label>
            <select className="rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-primary)] px-3 py-2 text-sm w-32 focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]"
              value={searchCategory} onChange={(e) => setSearchCategory(e.target.value)}>
              <option value="">All</option>
              {CATEGORIES.map((c) => (<option key={c} value={c}>{c}</option>))}
            </select>
          </div>
          <div className="flex gap-2">
            <Button type="submit" variant="primary">Search</Button>
            <Button type="button" variant="secondary" onClick={handleClear}>Clear</Button>
          </div>
        </form>
      </Card>

      {error && (
        <div className="mb-6 rounded-lg border border-[var(--color-danger)]/30 bg-[var(--color-danger-light)] px-4 py-3 text-sm text-[var(--color-danger)]">{error}</div>
      )}

      {loading ? (
        <div className="flex justify-center py-20">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-[var(--color-border)] border-t-[var(--color-accent)]" />
        </div>
      ) : (
        <Card hover={false} className="overflow-hidden !p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[var(--color-border)] bg-[var(--color-bg-secondary)]">
                  <th className="px-4 py-3 text-left font-medium">Make</th>
                  <th className="px-4 py-3 text-left font-medium">Model</th>
                  <th className="px-4 py-3 text-left font-medium">Category</th>
                  <th className="px-4 py-3 text-right font-medium">Price</th>
                  <th className="px-4 py-3 text-right font-medium">Qty</th>
                  <th className="px-4 py-3 text-right font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {vehicles.length === 0 && (
                  <tr><td colSpan={6} className="px-4 py-12 text-center text-[var(--color-text-secondary)]">No vehicles found</td></tr>
                )}
                {vehicles.map((v, i) => (
                  <tr key={v.id} className={`border-b border-[var(--color-border)] last:border-0 transition-colors hover:bg-[var(--color-accent-light)]/30 ${i % 2 === 1 ? "bg-[var(--color-bg-secondary)]/30" : ""}`}>
                    <td className="px-4 py-3 font-medium">{v.make}</td>
                    <td className="px-4 py-3">{v.model}</td>
                    <td className="px-4 py-3">
                      <span className="rounded-full bg-[var(--color-accent-light)] px-2 py-0.5 text-xs font-medium text-[var(--color-accent)]">{v.category}</span>
                    </td>
                    <td className="px-4 py-3 text-right font-medium">₹{Number(v.price).toLocaleString("en-IN")}</td>
                    <td className="px-4 py-3 text-right">{v.quantity}</td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex justify-end gap-1">
                        <Button variant="ghost" onClick={() => openEdit(v)}>Edit</Button>
                        <Button variant="ghost" onClick={() => { setRestockId(v.id); setRestockQty("1"); }}>Restock</Button>
                        <Button variant="ghost" onClick={() => setDeleteId(v.id)}>
                          <span className="text-[var(--color-danger)]">Delete</span>
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      <Modal open={addOpen} onClose={() => setAddOpen(false)} title="Add Vehicle">
        <VehicleForm form={form} setForm={setForm} error={formError} onSubmit={handleAdd} submitting={submitting} submitLabel="Add Vehicle" onCancel={() => setAddOpen(false)} />
      </Modal>
      <Modal open={editOpen} onClose={() => setEditOpen(false)} title="Edit Vehicle">
        <VehicleForm form={form} setForm={setForm} error={formError} onSubmit={handleEdit} submitting={submitting} submitLabel="Save Changes" onCancel={() => setEditOpen(false)} />
      </Modal>
      <Modal open={deleteId !== null} onClose={() => setDeleteId(null)} title="Delete Vehicle">
        <p className="mb-4 text-sm text-[var(--color-text-secondary)]">Are you sure you want to delete this vehicle?</p>
        <div className="flex justify-end gap-2">
          <Button variant="secondary" onClick={() => setDeleteId(null)}>Cancel</Button>
          <Button variant="danger" onClick={handleDelete}>Delete</Button>
        </div>
      </Modal>
      <Modal open={restockId !== null} onClose={() => setRestockId(null)} title="Restock Vehicle">
        <div className="flex flex-col gap-4">
          <Input label="Quantity to add" type="number" min={1} value={restockQty} onChange={(e) => setRestockQty(e.target.value)} />
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setRestockId(null)}>Cancel</Button>
            <Button onClick={handleRestock}>Restock</Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}

function VehicleForm({ form, setForm, error, onSubmit, submitting, submitLabel, onCancel }: {
  form: FormData; setForm: (f: FormData) => void; error: string; onSubmit: (e: FormEvent) => void;
  submitting: boolean; submitLabel: string; onCancel: () => void;
}) {
  return (
    <form onSubmit={onSubmit} className="flex flex-col gap-4">
      <div className="grid grid-cols-2 gap-4">
        <Input label="Make" value={form.make} onChange={(e) => setForm({ ...form, make: e.target.value })} placeholder="Toyota" />
        <Input label="Model" value={form.model} onChange={(e) => setForm({ ...form, model: e.target.value })} placeholder="Camry" />
      </div>
      <div>
        <label className="mb-1.5 block text-sm font-medium">Category</label>
        <select className="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-primary)] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]"
          value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value as VehicleCategory })}>
          {CATEGORIES.map((c) => (<option key={c} value={c}>{c}</option>))}
        </select>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <Input label="Price (₹)" type="number" min={0} step="0.01" value={form.price} onChange={(e) => setForm({ ...form, price: e.target.value })} placeholder="25000" />
        <Input label="Quantity" type="number" min={0} value={form.quantity} onChange={(e) => setForm({ ...form, quantity: e.target.value })} placeholder="10" />
      </div>
      {error && <p className="text-sm text-[var(--color-danger)]">{error}</p>}
      <div className="flex justify-end gap-2 pt-2">
        <Button variant="secondary" type="button" onClick={onCancel}>Cancel</Button>
        <Button type="submit" loading={submitting}>{submitLabel}</Button>
      </div>
    </form>
  );
}
