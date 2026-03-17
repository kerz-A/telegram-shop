import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { CartProvider } from "./context/CartContext";
import CatalogPage from "./pages/Catalog";
import CartPage from "./pages/Cart";
import CheckoutPage from "./pages/Checkout";

export default function App() {
  return (
    <CartProvider>
      <BrowserRouter>
        <div className="app">
          <Routes>
            <Route path="/" element={<CatalogPage />} />
            <Route path="/cart" element={<CartPage />} />
            <Route path="/checkout" element={<CheckoutPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </div>
      </BrowserRouter>
    </CartProvider>
  );
}
