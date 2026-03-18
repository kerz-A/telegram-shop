import type { Product } from "../api/client";

interface Props {
  product: Product;
  onAddToCart: (productId: number) => void;
  onClick: (productId: number) => void;
  adding?: boolean;
  cartQuantity?: number;
}

const PLACEHOLDER = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Crect fill='%23ddd' width='200' height='200'/%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' fill='%23999' font-size='14'%3EНет фото%3C/text%3E%3C/svg%3E";

export default function ProductCard({ product, onAddToCart, onClick, adding, cartQuantity }: Props) {
  const btnText = adding
    ? "✓ Добавлено"
    : cartQuantity
    ? `В корзине: ${cartQuantity}`
    : "В корзину";

  return (
    <div className="product-card" onClick={() => onClick(product.id)}>
      <img src={product.first_image || PLACEHOLDER} alt={product.name} loading="lazy" />
      <div className="info">
        <div className="name">{product.name}</div>
        <div className="price">{product.price} ₽</div>
        <button
          className="qty-btn"
          style={{
            width: "100%",
            borderRadius: 10,
            marginTop: 8,
            height: 36,
            fontSize: 14,
            background: adding ? "#4CAF50" : cartQuantity ? "#2196F3" : undefined,
            color: adding || cartQuantity ? "#fff" : undefined,
            transition: "background 0.3s",
          }}
          onClick={(e) => {
            e.stopPropagation();
            onAddToCart(product.id);
          }}
        >
          {btnText}
        </button>
      </div>
    </div>
  );
}
