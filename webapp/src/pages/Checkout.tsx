import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { orderApi, profileApi, type CustomerProfile } from "../api/client";
import { useCart } from "../context/CartContext";
import { useTelegram } from "../hooks/useTelegram";

export default function CheckoutPage() {
  const [profile, setProfile] = useState<CustomerProfile | null>(null);
  const [fullName, setFullName] = useState("");
  const [address, setAddress] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const { showMainButton, hideMainButton, showBackButton, hideBackButton, webApp } = useTelegram();
  const { refreshCart } = useCart();
  const navigate = useNavigate();

  // Load profile for phone
  useEffect(() => {
    profileApi.get().then(setProfile).catch(console.error);
  }, []);

  // Back button
  useEffect(() => {
    showBackButton(() => navigate("/cart"));
    return () => hideBackButton();
  }, [navigate, showBackButton, hideBackButton]);

  // Submit handler
  const handleSubmit = useCallback(async () => {
    if (!fullName.trim()) {
      setError("Укажите ФИО");
      return;
    }
    if (!address.trim()) {
      setError("Укажите адрес доставки");
      return;
    }
    setError("");
    setSubmitting(true);

    try {
      const order = await orderApi.create({
        full_name: fullName.trim(),
        address: address.trim(),
      });
      await refreshCart();
      webApp?.showAlert(`Заказ #${order.id} оформлен! Ожидайте подтверждения.`, () => {
        webApp?.close();
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Ошибка оформления заказа";
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  }, [fullName, address, refreshCart, webApp]);

  // Main button
  useEffect(() => {
    if (!submitting) {
      showMainButton("Подтвердить заказ", handleSubmit);
    }
    return () => hideMainButton();
  }, [handleSubmit, submitting, showMainButton, hideMainButton]);

  return (
    <div>
      <h1 className="page-title">Оформление заказа</h1>

      {error && (
        <div style={{ color: "var(--tg-theme-destructive-text-color, #e53935)", marginBottom: 12, fontSize: 14 }}>
          ❌ {error}
        </div>
      )}

      <div className="form-group">
        <label>Телефон</label>
        <input type="tel" value={profile?.phone || ""} disabled />
      </div>

      <div className="form-group">
        <label>ФИО</label>
        <input
          type="text"
          placeholder="Иванов Иван Иванович"
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
        />
      </div>

      <div className="form-group">
        <label>Адрес доставки</label>
        <textarea
          placeholder="Город, улица, дом, квартира"
          value={address}
          onChange={(e) => setAddress(e.target.value)}
        />
      </div>

      {submitting && <div className="loading">Оформляем заказ...</div>}
    </div>
  );
}
