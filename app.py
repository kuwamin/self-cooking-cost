from flask import Flask, render_template, request, redirect, url_for, jsonify
import json
import os
import pykakasi

app = Flask(__name__)
kks = pykakasi.kakasi()

ING_FILE = "ingredients.json"
REC_FILE = "recipes.json"

MEMO_TEXT = (
    "\U0001F4A1 使用量の参考メモ：\n"
    "・大さじ1 = 約15ml\n"
    "・小さじ1 = 約5ml\n"
    "・1カップ = 約200ml\n"
)

# -------------------- データ読み込み --------------------
def load_json(file):
    if os.path.exists(file):
        with open(file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

ingredients_db = load_json(ING_FILE)
recipes_db = load_json(REC_FILE)

# -------------------- 保存処理 --------------------
def save_json(file, data):
    with open(file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# -------------------- ソート用よみがな取得 --------------------
def get_hiragana_reading(text):
    result = kks.convert(text)
    return ''.join([item['hira'] for item in result])

# -------------------- コスト計算 --------------------
def calculate_costs():
    recipe_costs = {}
    for name, data in recipes_db.items():
        total = 0
        for ing_name, amount in data.get("ingredients", []):
            info = ingredients_db.get(ing_name)
            if info:
                unit_price = info['price'] / info['quantity']
                total += unit_price * amount
        servings = data.get("servings", 1)
        per_serving = total / servings if servings > 0 else 0
        recipe_costs[name] = {
            'total': round(total),
            'per_serving': round(per_serving)
        }
    return recipe_costs

# -------------------- ルート：トップページ --------------------
@app.route('/')
def index():
    sorted_ingredients = sorted(ingredients_db.items(), key=lambda x: get_hiragana_reading(x[0]))
    sorted_recipes = sorted(recipes_db.items(), key=lambda x: get_hiragana_reading(x[0]))

    recipe_costs = {}
    for name, data in sorted_recipes:
        total = 0
        for ing_name, amount in data["ingredients"]:
            info = ingredients_db.get(ing_name)
            if info:
                unit_price = info['price'] / info['quantity']
                total += unit_price * amount
        servings = data.get("servings", 1)
        per_serving = total / servings if servings > 0 else 0
        recipe_costs[name] = {
            "total": round(total),
            "per_serving": round(per_serving)
        }

    return render_template(
        'index.html',
        ingredients=sorted_ingredients,
        recipes=sorted_recipes,
        ingredients_dict=ingredients_db,
        recipe_costs=recipe_costs,  # ← 追加
        memo=MEMO_TEXT              # ← メモもちゃんと渡す
    )



# -------------------- 食材追加 --------------------
@app.route('/add_ingredient', methods=['POST'])
def add_ingredient():
    name = request.form['name']
    price = float(request.form['price'])
    quantity = float(request.form['quantity'])
    unit = request.form['unit']
    ingredients_db[name] = {'price': price, 'quantity': quantity, 'unit': unit}
    save_json(ING_FILE, ingredients_db)
    return redirect(url_for('index'))

# -------------------- 食材編集フォーム表示 --------------------
@app.route('/edit_ingredient/<name>')
def edit_ingredient_form(name):
    ing = ingredients_db.get(name)
    return render_template('edit_ingredient.html', name=name, data=ing)

# -------------------- 食材編集実行 --------------------
@app.route('/update_ingredient', methods=['POST'])
def update_ingredient_post():
    name = request.form['name']
    price = float(request.form['price'])
    quantity = float(request.form['quantity'])
    unit = request.form['unit']
    ingredients_db[name] = {'price': price, 'quantity': quantity, 'unit': unit}
    save_json(ING_FILE, ingredients_db)
    return redirect(url_for('index'))

# -------------------- 食材削除 --------------------
@app.route('/delete_ingredient', methods=['POST'])
def delete_ingredient():
    name = request.form['name']
    if name in ingredients_db:
        del ingredients_db[name]
        save_json(ING_FILE, ingredients_db)
    return redirect(url_for('index'))

# -------------------- 食材編集画面を表示 --------------------
@app.route('/edit_ingredient/<name>', methods=['POST'])
def update_ingredient(name):
    price = float(request.form['price'])
    quantity = float(request.form['quantity'])
    unit = request.form['unit']
    ingredients_db[name] = {'price': price, 'quantity': quantity, 'unit': unit}
    save_json(ING_FILE, ingredients_db)
    return redirect(url_for('index'))

# -------------------- 食材情報を更新 --------------------
@app.route('/update_ingredient/<name>', methods=['POST'])
def update_ingredient_named(name):
    if name not in ingredients_db:
        return f"{name} は登録されていません", 404
    try:
        price = float(request.form['price'])
        quantity = float(request.form['quantity'])
        unit = request.form['unit']
    except:
        return "入力が不正です", 400

    ingredients_db[name] = {'price': price, 'quantity': quantity, 'unit': unit}
    save_json(ING_FILE, ingredients_db)
    return redirect(url_for('index'))



# -------------------- 料理追加 --------------------
@app.route('/add_recipe', methods=['POST'])
def add_recipe():
    name = request.form['recipe_name']
    servings = int(request.form['servings'])
    ingredients = []
    names = request.form.getlist('ing_name')
    amounts = request.form.getlist('ing_amount')
    for n, a in zip(names, amounts):
        try:
            ingredients.append((n, float(a)))
        except:
            continue
    recipes_db[name] = {"ingredients": ingredients, "servings": servings}
    save_json(REC_FILE, recipes_db)
    return redirect(url_for('index'))

# -------------------- 料理編集フォーム表示 --------------------
@app.route('/edit_recipe/<name>')
def edit_recipe_form(name):
    recipe = recipes_db.get(name)
    return render_template(
        'edit_recipe.html',
        name=name,
        data=recipe,
        ingredients=list(ingredients_db.keys()),
        ingredients_db=ingredients_db
    )

# -------------------- 料理編集実行 --------------------
@app.route('/update_recipe/<name>', methods=['POST'])
def update_recipe(name):
    servings = int(request.form['servings'])
    ing_names = request.form.getlist('ing_name')
    ing_amounts = request.form.getlist('ing_amount')
    ingredients = []
    for n, a in zip(ing_names, ing_amounts):
        try:
            ingredients.append((n, float(a)))
        except:
            continue
    recipes_db[name] = {
        "ingredients": ingredients,
        "servings": servings
    }
    save_json(REC_FILE, recipes_db)
    return redirect(url_for('index'))

# -------------------- 料理削除 --------------------
@app.route('/delete_recipe/<name>')
def delete_recipe(name):
    if name in recipes_db:
        del recipes_db[name]
        save_json(REC_FILE, recipes_db)
    return redirect(url_for('index'))

# -------------------- 料理編集フォーム表示 --------------------
@app.route('/edit_recipe/<name>')
def edit_recipe(name):
    data = recipes_db.get(name)
    if not data:
        return f"{name} は登録されていません", 404
    return render_template('edit_recipe.html', name=name, data=data)

# -------------------- 料理更新処理 --------------------
@app.route('/update_recipe/<name>', methods=['POST'])
def update_recipe_post(name):
    try:
        servings = int(request.form['servings'])
        names = request.form.getlist('ing_name')
        amounts = request.form.getlist('ing_amount')
        ingredients = [(n, float(a)) for n, a in zip(names, amounts)]
        recipes_db[name] = {
            'ingredients': ingredients,
            'servings': servings
        }
        save_json(REC_FILE, recipes_db)
        return redirect(url_for('index'))
    except:
        return "入力エラーが発生しました", 400


# -------------------- 料理削除処理 --------------------
@app.route('/delete_recipe', methods=['POST'])
def delete_recipe_post():
    name = request.form['name']
    if name in recipes_db:
        del recipes_db[name]
        save_json(REC_FILE, recipes_db)
    return redirect(url_for('index'))


# -------------------- コスト計算API --------------------
@app.route('/get_recipe_cost/<recipe_name>')
def get_recipe_cost(recipe_name):
    data = recipes_db.get(recipe_name)
    if not data:
        return jsonify({'error': 'not found'})
    items = data['ingredients']
    servings = data.get('servings', 1)
    total_cost = 0
    details = []
    for ing_name, amount in items:
        info = ingredients_db.get(ing_name)
        if not info:
            details.append(f"{ing_name}: 未登録")
            continue
        unit_price = info['price'] / info['quantity']
        cost = unit_price * amount
        total_cost += cost
        details.append(f"{ing_name}: {amount}{info['unit']} × {unit_price:.2f}円 = {cost:.2f}円")
    per_serving = total_cost / servings if servings > 0 else 0
    return jsonify({
        'total': round(total_cost),
        'per_serving': round(per_serving),
        'details': details
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)

