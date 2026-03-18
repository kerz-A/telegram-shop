import axios from "axios";
import { getInitData } from "../utils/telegram";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api";

const api = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
});

// Inject Telegram initData on every request
api.interceptors.request.use((config) => {
  const initData = getInitData();
  if (initData) {
    config.headers.Authorization = `tma ${initData}`;
  }
  return config;
});

// ─── Types ─────────────────────────────────────────────────────────

export interface ProductImage {
  id: number;
  image: string;
  sort_order: number;
}

export interface Product {
  id: number;
  name: string;
  description?: string;
  price: string;
  category: number;
  category_name: string;
  first_image?: string;
  images?: ProductImage[];
}

export interface Category {
  id: number;
  name: string;
  slug: string;
  parent: number | null;
  children: Category[];
  product_count: number;
}

export interface CartItem {
  id: number;
  product: Product;
  product_id: number;
  quantity: number;
  total: string;
}

export interface CartResponse {
  items: CartItem[];
  total: string;
}

export interface OrderItem {
  id: number;
  product_name: string;
  price: string;
  quantity: number;
  total: string;
}

export interface Order {
  id: number;
  status: string;
  status_display: string;
  full_name: string;
  phone: string;
  address: string;
  total: string;
  items: OrderItem[];
  created_at: string;
}

export interface CustomerProfile {
  telegram_id: number;
  username: string;
  first_name: string;
  phone: string;
}

// ─── API Methods ───────────────────────────────────────────────────

export const categoryApi = {
  list: () =>
    api.get("/categories/").then((r) => {
      const data = r.data;
      return Array.isArray(data) ? data : data.results ?? [];
    }),
};

export const productApi = {
  list: (params?: { category?: number; search?: string }) =>
    api.get("/products/", { params }).then((r) => {
      const data = r.data;
      return Array.isArray(data) ? data : data.results ?? [];
    }),
  detail: (id: number) => api.get<Product>(`/products/${id}/`).then((r) => r.data),
};

export const cartApi = {
  get: () => api.get<CartResponse>("/cart/").then((r) => r.data),
  update: (product_id: number, quantity: number) =>
    api.post("/cart/", { product_id, quantity }),
  clear: () => api.delete("/cart/"),
};

export const orderApi = {
  list: () =>
    api.get("/orders/").then((r) => {
      const data = r.data;
      return Array.isArray(data) ? data : data.results ?? [];
    }),
  create: (data: { full_name: string; address: string }) =>
    api.post<Order>("/orders/create/", data).then((r) => r.data),
};

export const profileApi = {
  get: () => api.get<CustomerProfile>("/profile/").then((r) => r.data),
};

export default api;
