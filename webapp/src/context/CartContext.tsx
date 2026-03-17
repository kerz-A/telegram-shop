import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from "react";
import { cartApi, type CartItem, type CartResponse } from "../api/client";

interface CartContextType {
  items: CartItem[];
  total: string;
  loading: boolean;
  refreshCart: () => Promise<void>;
  updateItem: (productId: number, quantity: number) => Promise<void>;
  clearCart: () => Promise<void>;
  itemCount: number;
}

const CartContext = createContext<CartContextType | null>(null);

export function CartProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<CartItem[]>([]);
  const [total, setTotal] = useState("0");
  const [loading, setLoading] = useState(true);

  const refreshCart = useCallback(async () => {
    try {
      setLoading(true);
      const data: CartResponse = await cartApi.get();
      setItems(data.items);
      setTotal(data.total);
    } catch (err) {
      console.error("Failed to load cart:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  const updateItem = useCallback(
    async (productId: number, quantity: number) => {
      try {
        await cartApi.update(productId, quantity);
        await refreshCart();
      } catch (err) {
        console.error("Failed to update cart:", err);
      }
    },
    [refreshCart]
  );

  const clearCart = useCallback(async () => {
    try {
      await cartApi.clear();
      setItems([]);
      setTotal("0");
    } catch (err) {
      console.error("Failed to clear cart:", err);
    }
  }, []);

  useEffect(() => {
    refreshCart();
  }, [refreshCart]);

  const itemCount = items.reduce((sum, item) => sum + item.quantity, 0);

  return (
    <CartContext.Provider
      value={{ items, total, loading, refreshCart, updateItem, clearCart, itemCount }}
    >
      {children}
    </CartContext.Provider>
  );
}

export function useCart(): CartContextType {
  const ctx = useContext(CartContext);
  if (!ctx) throw new Error("useCart must be used inside CartProvider");
  return ctx;
}
