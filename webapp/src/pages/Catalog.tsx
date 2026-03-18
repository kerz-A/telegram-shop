import { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { categoryApi, productApi, type Category, type Product } from "../api/client";
import { useCart } from "../context/CartContext";
import ProductCard from "../components/ProductCard";

export default function CatalogPage() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<number | null>(null);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [addingId, setAddingId] = useState<number | null>(null);
  const { items, updateItem } = useCart();
  const navigate = useNavigate();

  useEffect(() => {
    categoryApi.list().then(setCategories).catch(console.error);
  }, []);

  const loadProducts = useCallback(async () => {
    setLoading(true);
    try {
      const params: { category?: number; search?: string } = {};
      if (selectedCategory) params.category = selectedCategory;
      if (search.trim()) params.search = search.trim();
      const data = await productApi.list(params);
      setProducts(data);
    } catch (err) {
      console.error("Failed to load products:", err);
    } finally {
      setLoading(false);
    }
  }, [selectedCategory, search]);

  useEffect(() => {
    const timer = setTimeout(loadProducts, 300);
    return () => clearTimeout(timer);
  }, [loadProducts]);

  const handleAddToCart = async (productId: number) => {
    setAddingId(productId);
    const existing = items.find((i) => i.product.id === productId);
    const newQty = (existing?.quantity || 0) + 1;
    await updateItem(productId, newQty);
    setTimeout(() => setAddingId(null), 800);
  };

  return (
    <div>
      <h1 className="page-title">Каталог</h1>

      <input
        className="search-bar"
        type="text"
        placeholder="🔍 Поиск товаров..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />

      <div className="categories">
        <button
          className={`category-chip ${selectedCategory === null ? "active" : ""}`}
          onClick={() => setSelectedCategory(null)}
        >
          Все
        </button>
        {categories.map((cat) => (
          <button
            key={cat.id}
            className={`category-chip ${selectedCategory === cat.id ? "active" : ""}`}
            onClick={() => setSelectedCategory(cat.id)}
          >
            {cat.name}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="loading">Загрузка...</div>
      ) : products.length === 0 ? (
        <div className="empty-state">
          <div className="icon">🔍</div>
          <p>Товары не найдены</p>
        </div>
      ) : (
        <div className="product-grid">
          {products.map((product) => {
            const cartItem = items.find((i) => i.product.id === product.id);
            return (
              <ProductCard
                key={product.id}
                product={product}
                onAddToCart={handleAddToCart}
                onClick={() => {}}
                adding={addingId === product.id}
                cartQuantity={cartItem?.quantity}
              />
            );
          })}
        </div>
      )}

      {/* Floating cart button */}
      {items.length > 0 && (
        <div
          style={{
            position: "fixed",
            bottom: 16,
            left: 16,
            right: 16,
            zIndex: 100,
          }}
        >
          <button
            onClick={() => navigate("/cart")}
            style={{
              width: "100%",
              padding: "14px",
              borderRadius: 12,
              border: "none",
              background: "var(--tg-theme-button-color, #2196F3)",
              color: "var(--tg-theme-button-text-color, #fff)",
              fontSize: 16,
              fontWeight: 500,
              cursor: "pointer",
              boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
            }}
          >
            🛒 Корзина · {items.reduce((s, i) => s + i.quantity, 0)} шт.
          </button>
        </div>
      )}
    </div>
  );
}
