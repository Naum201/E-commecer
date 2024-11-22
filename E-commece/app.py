from flask import Flask, render_template, request, redirect, url_for, flash, session, current_app, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import os
import qrcode
from io import BytesIO

app = Flask(__name__)
app.secret_key = "sua_chave_secreta_aqui"

# Configuração do banco de dados MySQL
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql://root:@localhost/LOJA_ECOMMERCER"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Modelos do banco de dados
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    image_url = db.Column(db.String(200), nullable=True)  # Novo campo para URL da imagem
    is_active = db.Column(db.Boolean, default=True)  # Novo campo para status do produto

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    product = db.relationship("Product", backref="carts")

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    total_amount = db.Column(db.Float, nullable=False)
    is_completed = db.Column(db.Boolean, default=False)
    user = db.relationship('User', backref='orders')
    # Add other fields as needed (e.g., shipping address, payment info, etc.)

# Cria o banco de dados
with app.app_context():
    db.create_all()

# Rota: Home
@app.route("/")
def home():
    return render_template("home.html")

# Rota de Login do Usuário
@app.route("/login_user", methods=["GET", "POST"])
def login_user():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            return redirect(url_for("home"))
        flash("Credenciais inválidas")
    return render_template("login.html")

# Rota de Login do Administrador
@app.route("/login_admin", methods=["GET", "POST"])
def login_admin():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        admin = Admin.query.filter_by(email=email).first()
        if admin and check_password_hash(admin.password, password):
            session["admin_id"] = admin.id
            return redirect(url_for("admin"))
        flash("Credenciais inválidas")
    return render_template("login_admin.html")

# Rota de Cadastro do Usuário
@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])
        new_user = User(username=username, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash("Cadastro realizado com sucesso!")
        return redirect(url_for("loja"))  # Alterado para login_user
    return render_template("cadastro.html")

# Rota de Cadastro do Administrador
@app.route("/cadastro_admin", methods=["GET", "POST"])
def cadastro_admin():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])
        new_admin = Admin(username=username, email=email, password=password)
        db.session.add(new_admin)
        db.session.commit()
        flash("Cadastro realizado com sucesso!")
        return redirect(url_for("loja"))  # Alterado para login_admin
    return render_template("cadastro_admin.html")

# Rota: Loja
@app.route("/loja")
def loja():
    products = Product.query.all()
    return render_template("loja.html", products=products)

# Rota de Cadastro de Item
@app.route("/item_cadastro", methods=["GET", "POST"])
def item_cadastro():
    if request.method == "POST":
        # Captura os dados do formulário
        name = request.form["name"]
        description = request.form["description"]
        price = float(request.form["price"])
        stock = int(request.form["stock"])
        
        # Upload da imagem
        image = request.files["image"]
        image_url = None
        if image and image.filename != '':
            filename = secure_filename(image.filename)
            image_path = os.path.join('static/images', filename)
            full_image_path = os.path.join(current_app.root_path, image_path)
            
            # Salva a imagem na pasta `static/images`
            image.save(full_image_path)
            image_url = f"/{image_path}"
        
        # Cria o novo produto no banco
        new_product = Product(name=name, description=description, price=price, stock=stock, image_url=image_url)
        db.session.add(new_product)
        db.session.commit()
        
        flash("Produto cadastrado com sucesso!")
        return redirect(url_for("loja"))
    
    return render_template("item_cadastro.html")

# Rota: Produto Detalhado
@app.route("/produto_detalhado/<int:id>")
def produto_detalhado(id):
    product = Product.query.get_or_404(id)
    return render_template("produto_detalhado.html", product=product)

@app.route("/carrinho")
def carrinho():
    user_id = session.get("user_id")
    if not user_id:
        flash("Você precisa estar logado para ver o carrinho.")
        return redirect(url_for("login_user"))
    
    cart_items = Cart.query.filter_by(user_id=user_id).all()
    total_price = sum(
        item.product.price * item.quantity for item in cart_items if item.product.is_active
    )
    return render_template("carrinho.html", cart_items=cart_items, total_price=total_price)
    
@app.route("/remove_item/<int:item_id>")
def remove_item(item_id):
    item = Cart.query.get(item_id)
    if item and item.user_id == session.get("user_id"):
        db.session.delete(item)
        db.session.commit()
        flash("Item removido do carrinho com sucesso!")
    return redirect(url_for("carrinho"))


# Rota: Checkout
@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    if request.method == "POST":
        # Coleta dados do formulário
        nome = request.form["nome"]
        endereco = request.form["endereco"]
        forma_pagamento = request.form["forma_pagamento"]
        flash("Checkout realizado com sucesso!")
        return redirect(url_for("home"))

    return render_template("checkout.html")

# Função para gerar a string do Pix (COPIA E COLA) padrão QR Code BR Code do Bacen
def gerar_payload_pix(chave, nome_recebedor, cidade_recebedor, valor, descricao="Pagamento via Pix"):
    # Parâmetros obrigatórios do payload
    payload = f"""
    000201
    26{len(chave) + 7}0014BR.GOV.BCB.PIX01{len(chave):02}{chave}  
    52040000
    5303986
    5802BR
    59{len(nome_recebedor):02}{nome_recebedor}
    60{len(cidade_recebedor):02}{cidade_recebedor}
    5405{int(valor * 100):02d}
    62070503***""".replace(" ", "").replace("\n", "")  # Remove espaços em branco e novas linhas

    # Calcula o CRC16
    crc = f"{calcular_crc16(payload + '6304'):04X}"
    return payload + "6304" + crc

# Função para calcular o CRC16 para QR Code Pix
def calcular_crc16(payload):
    crc = 0xFFFF
    for byte in bytearray(payload, "utf-8"):
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0x8408 if crc & 1 else crc >> 1
    return crc & 0xFFFF

# Função para gerar o QR Code
def gerar_qrcode(payload):
    qr = qrcode.make(payload)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer

# Rota de checkout com geração de QR Code para pagamento via Pix
@app.route("/checkout_pix", methods=["POST"])
def finalizar_compra():
    nome = request.form["nome"]
    endereco = request.form["endereco"]
    forma_pagamento = request.form["forma_pagamento"]
    chave_pix = "email@exemplo.com"  # Use o telefone, chave aleatória ou e-mail do recebedor
    nome_recebedor = "Nome Recebedor"
    cidade_recebedor = "Cidade"
    
    # Aqui deve ter a lógica para calcular o valor total
    valor = 10.0  # Por exemplo, um valor fixo para testes

    # Gera a string Pix e o QR Code
    payload_pix = gerar_payload_pix(chave_pix, nome_recebedor, cidade_recebedor, valor)
    qr_code = gerar_qrcode(payload_pix)

    # Redireciona para a visualização do QR Code gerado
    return send_file(qr_code, mimetype="image/png", as_attachment=True, download_name="qrcode_pix.png")
# Rota para Gerenciar Produtos
@app.route("/produtos", methods=["GET"])
def produtos():
    products = Product.query.all()  # Retrieve all products
    total_products = Product.query.count()
    active_products = Product.query.filter_by(is_active=True).count()
    inactive_products = Product.query.filter_by(is_active=False).count()
    return render_template("produtos.html", products=products,  total=total_products, active=active_products, inactive=inactive_products)

# Rota para Gerenciar Clientes
@app.route("/clientes", methods=["GET"])
def clientes():
    users = User.query.all()  # Retrieve all users
    return render_template("clientes.html", users=users)

# Rota para Gerenciar Pedidos
@app.route("/pedidos", methods=["GET"])
def pedidos():
    orders = Order.query.all()  # Retrieve all orders
    return render_template("pedidos.html", orders=orders)

# Rota: Admin
@app.route("/admin")
def admin():
    if "admin_id" not in session:
        flash("Acesso negado!")
        return redirect(url_for("home"))
    users = User.query.all()
    products = Product.query.all()
    return render_template("admin.html", users=users, products=products)

# Rota de Perfil
@app.route("/perfil", methods=["GET", "POST"])
def perfil():
    if "user_id" not in session:
        flash("Por favor, faça login para acessar seu perfil.")
        return redirect(url_for("login_user"))

    user = User.query.get(session["user_id"])
    
    if request.method == "POST":
        # Coletar e atualizar as informações do perfil
        user.username = request.form["username"]
        user.email = request.form["email"]
        
        # Atualizar a senha se o usuário forneceu uma nova
        if request.form["password"]:
            user.password = generate_password_hash(request.form["password"])

        db.session.commit()
        flash("Perfil atualizado com sucesso!")
        return redirect(url_for("perfil"))

    return render_template("perfil.html", user=user)

if __name__ == "__main__":
    app.run(debug=True)
