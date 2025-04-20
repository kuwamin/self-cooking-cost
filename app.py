from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os
import pykakasi
from flask import flash, get_flashed_messages

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.getenv("SECRET_KEY")


db = SQLAlchemy(app)
kks = pykakasi.kakasi()

# -------------------- メモ --------------------
memo_text = (
    "\U0001F4A1 使用量の参考メモ：\n"
    "・大さじ1 = 約15ml\n"
    "・小さじ1 = 約5ml\n"
    "・1カップ = 約200ml\n"
    "・固体の大さじ1 = 9g\n"
    "version:1.0.3"
)

# -------------------- モデル定義 --------------------
class Ingredient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20), nullable=False)

class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    servings = db.Column(db.Integer, nullable=False)

class RecipeIngredient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'))
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredient.id'))
    amount = db.Column(db.Float, nullable=False)

# -------------------- よみがな --------------------
def get_hiragana_reading(text):
    result = kks.convert(text)
    return ''.join([item['hira'] for item in result])

# -------------------- トップページ --------------------
@app.route('/')
def index():
    ingredients = Ingredient.query.all()
    recipes = Recipe.query.all()
    recipe_costs = {}
    for recipe in recipes:
        links = RecipeIngredient.query.filter_by(recipe_id=recipe.id).all()
        total = 0
        for link in links:
            ingredient = Ingredient.query.get(link.ingredient_id)
            if ingredient:
                unit_price = ingredient.price / ingredient.quantity
                total += unit_price * link.amount
        per_serving = total / recipe.servings if recipe.servings > 0 else 0
        recipe_costs[recipe.id] = {'total': round(total), 'per_serving': round(per_serving)}

    ingredients_sorted = sorted(ingredients, key=lambda x: get_hiragana_reading(x.name))
    recipes_sorted = sorted(recipes, key=lambda x: get_hiragana_reading(x.name))
    return render_template(
        'index.html',
        ingredients=ingredients_sorted,
        recipes=recipes_sorted,
        recipe_costs=recipe_costs,
        memo=memo_text
    )

# -------------------- 食材追加 --------------------
@app.route('/add_ingredient', methods=['POST'])
def add_ingredient():
    name = request.form['name']
    price = float(request.form['price'])
    quantity = float(request.form['quantity'])
    unit = request.form['unit']
    new_ingredient = Ingredient(name=name, price=price, quantity=quantity, unit=unit)
    db.session.add(new_ingredient)
    db.session.commit()
    return redirect(url_for('index'))

# -------------------- 食材編集 --------------------
@app.route('/edit_ingredient/<int:id>')
def edit_ingredient_form(id):
    ingredient = Ingredient.query.get_or_404(id)
    return render_template('edit_ingredient.html', ingredient=ingredient)

@app.route('/update_ingredient/<int:id>', methods=['POST'])
def update_ingredient(id):
    ingredient = Ingredient.query.get_or_404(id)
    ingredient.price = float(request.form['price'])
    ingredient.quantity = float(request.form['quantity'])
    ingredient.unit = request.form['unit']
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete_ingredient', methods=['POST'])
def delete_ingredient():
    id = int(request.form['id'])
    ingredient = Ingredient.query.get(id)

    # 関連する料理があれば削除をブロック
    if RecipeIngredient.query.filter_by(ingredient_id=id).first():
        flash("この食材は料理に使用されています。削除できません。")
        return redirect(url_for('index'))

    if ingredient:
        db.session.delete(ingredient)
        db.session.commit()
    return redirect(url_for('index'))


# -------------------- 料理追加 --------------------
@app.route('/add_recipe', methods=['POST'])
def add_recipe():
    name = request.form['recipe_name']
    servings = int(request.form['servings'])
    recipe = Recipe(name=name, servings=servings)
    db.session.add(recipe)
    db.session.flush()  # ID取得のためコミット前にflush

    ing_ids = request.form.getlist('ing_id')  # ← 正しいキー名に修正！
    ing_amounts = request.form.getlist('ing_amount')
    for ing_id, amount in zip(ing_ids, ing_amounts):
        if ing_id and amount:
            link = RecipeIngredient(recipe_id=recipe.id, ingredient_id=int(ing_id), amount=float(amount))
            db.session.add(link)

    db.session.commit()
    return redirect(url_for('index'))


# -------------------- 料理編集 --------------------
@app.route('/edit_recipe/<int:id>')
def edit_recipe(id):
    recipe = Recipe.query.get_or_404(id)
    ingredients = Ingredient.query.all()
    links = RecipeIngredient.query.filter_by(recipe_id=recipe.id).all()
    return render_template('edit_recipe.html', name=recipe.name, data=recipe, ingredients=ingredients, ingredients_dict={i.id: i for i in ingredients}, links=links)

@app.route('/update_recipe/<name>', methods=['POST'])
def update_recipe_post(name):
    recipe = Recipe.query.filter_by(name=name).first_or_404()
    recipe.servings = int(request.form['servings'])
    RecipeIngredient.query.filter_by(recipe_id=recipe.id).delete()
    ing_ids = request.form.getlist('ing_id')
    ing_amounts = request.form.getlist('ing_amount')
    for ing_id, amount in zip(ing_ids, ing_amounts):
        db.session.add(RecipeIngredient(recipe_id=recipe.id, ingredient_id=int(ing_id), amount=float(amount)))
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete_recipe', methods=['POST'])
def delete_recipe():
    name = request.form['name']
    recipe = Recipe.query.filter_by(name=name).first()
    if recipe:
        RecipeIngredient.query.filter_by(recipe_id=recipe.id).delete()
        db.session.delete(recipe)
        db.session.commit()
    return redirect(url_for('index'))

# -------------------- コスト計算API --------------------
@app.route('/get_recipe_cost/<recipe_name>')
def get_recipe_cost(recipe_name):
    recipe = Recipe.query.filter_by(name=recipe_name).first()
    if not recipe:
        return jsonify({'error': 'not found'})
    items = RecipeIngredient.query.filter_by(recipe_id=recipe.id).all()
    servings = recipe.servings
    total_cost = 0
    details = []
    for item in items:
        ing = Ingredient.query.get(item.ingredient_id)
        if not ing:
            details.append(f"{item.ingredient_id}: 未登録")
            continue
        unit_price = ing.price / ing.quantity
        cost = unit_price * item.amount
        total_cost += cost
        details.append(f"{ing.name}: {item.amount}{ing.unit} × {unit_price:.2f}円 = {cost:.2f}円")
    per_serving = total_cost / servings if servings > 0 else 0
    return jsonify({
        'total': round(total_cost),
        'per_serving': round(per_serving),
        'details': details
    })

if __name__ == '__main__':
    app.run(debug=True)
