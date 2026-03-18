import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useCart } from "../context/CartContext";
import { useTelegram } from "../hooks/useTelegram";

export default function CartPage() {
  const { items, total, loading, updateItem, clearCart, refreshCart } = useCart();
  const { showMainButton, hideMainButton, showBackButton, hideBackButton } = useTelegram();
  const navigate = useNavigate();

  useEffect(() => {
    refreshCart();
  }, [refreshCart]);

  useEffect(() => {
    showBackButton(() => navigate("/"));
    return () => hideBackButton();
  }, [navigate, showBackButton, hideBackButton]);

  useEffect(() => {
    if (items.length > 0) {
      showMainButton(`Оформить заказ · ${total} ₽`, () => navigate("/checkout"));
      return () => hideMainButton();
    } else {
      hideMainButton();
    }
  }, [items, total, navigate, showMainButton, hideMainButton]);

  if (loading) return <div className="loading">Загрузка...</div>;

  if (items.length === 0) {
    return (
      <div>
        <h1 className="page-title">Корзина</h1>
        <div className="empty-state">
          <div className="icon">🛒</div>
          <p>Корзина пуста</p>
          <button
            onClick={() => navigate("/")}
            style={{
              marginTop: 16,
              padding: "12px 24px",
              borderRadius: 10,
              border: "none",
              background: "var(--tg-theme-button-color, #2196F3)",
              color: "var(--tg-theme-button-text-color, #fff)",
              fontSize: 15,
              cursor: "pointer",
            }}
          >
            Перейти в каталог
          </button>
        </div>
      </div>
    );
  }

  return (
    <div>
      <h1 className="page-title">Корзина</h1>

      {items.map((item) => (
        <div key={item.id} className="cart-item">
          <img
            src={item.product.first_image || ""}
            alt={item.product.name}
          />
          <div className="details">
            <div className="name">{item.product.name}</div>
            <div className="price">{item.product.price} ₽</div>
          </div>
          <div className="quantity-controls">
            <button
              className="qty-btn"
              onClick={() =>
                updateItem(
                  item.product.id,
                  item.quantity <= 1 ? 0 : item.quantity - 1
                )
              }
            >
              −
            </button>
            <span className="qty-value">{item.quantity}</span>
            <button
              className="qty-btn"
              onClick={() => updateItem(item.product.id, item.quantity + 1)}
            >
              +
            </button>
          </div>
        </div>
      ))}

      <div className="cart-total">Итого: {total} ₽</div>

      <button
        onClick={clearCart}
        style={{
          width: "100%",
          padding: "10px",
          background: "none",
          border: "1px solid var(--tg-theme-destructive-text-color, #e53935)",
          borderRadius: 10,
          color: "var(--tg-theme-destructive-text-color, #e53935)",
          fontSize: 14,
          cursor: "pointer",
        }}
      >
        Очистить корзину
      </button>
    </div>
  );
}
