f"""<div class="chatbot-table">
        <table>
            <thead>
                <th>Tên</th>
                <th>Giá</th>
                <th>Đặc điểm</th>
            </thead>
            <tbody>
                <tr>
                    <td><a href={url} target="_self">{name}</a></td>
                    <td>{price}</td>
                    <td>{specs}</td>
                </tr>
            </tbody>
        </table>
    <div>
    <div class="product-grid">
      <div class="product-card">
        <a href={url} class="product-image-wrapper">
          <img src={src} alt="NAME" class="product-image">
        </a>
        <div class="product-content">
          <a href={url} class="product-name">{name}</a>
          <div class="price-wrapper">
            <div class="price">{price}</div>
          </div>
        </div>
        <button class="add-to-cart-btn" onclick="window.open('URL', '_blank')">
          [SVG ICON]
          Thêm vào giỏ
        </button>
      </div>
    </div>"""
