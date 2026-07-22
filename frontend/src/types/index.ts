export interface User {
  id: number;
  email: string;
  username: string;
  role: "user" | "admin";
}

export interface Vehicle {
  id: number;
  make: string;
  model: string;
  category: VehicleCategory;
  price: string;
  quantity: number;
}

export type VehicleCategory =
  | "SUV"
  | "SEDAN"
  | "TRUCK"
  | "COUPE"
  | "HATCHBACK"
  | "VAN";

export interface AuthResponse {
  access_token: string;
  token_type: string;
}
