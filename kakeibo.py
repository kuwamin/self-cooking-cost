# --- ステップ1の食材DB ---
ingredients_db = {}

# 食材を登録する関数
def register_ingredient(name, price, quantity, unit):
    ingredients_db[name] = {
        'price': price,
        'quantity': quantity,
        'unit': unit
    }
    print(f"{name} を登録しました。")

# 食材を表示する関数
def show_all_ingredients():
    for name, info in ingredients_db.items():
        print(f"{name}: {info['price']}円 / {info['quantity']}{info['unit']}")
        

# --- ステップ2：料理DBと登録機能 ---
# 料理データを保存する辞書（キー: 料理名, 値: 食材と量のリスト）
recipes_db = {}

# 料理登録関数
def register_recipe(recipe_name, ingredients_list):
    """
    ingredients_list: [(食材名, 使用量), ...] 例: [("キャベツ", 1), ("たまねぎ", 2)]
    """
    recipes_db[recipe_name] = ingredients_list
    print(f"{recipe_name} を登録しました。")

# 登録済みの料理を表示する関数
def show_all_recipes():
    for recipe_name, items in recipes_db.items():
        print(f"\n{recipe_name}:")
        for ing_name, amount in items:
            unit = ingredients_db.get(ing_name, {}).get('unit', '不明')
            print(f"  - {ing_name}: {amount}{unit}")


# 料理のコストを計算する関数
def calculate_recipe_cost(recipe_name):
    if recipe_name not in recipes_db:
        print(f"{recipe_name} は登録されていません。")
        return

    total_cost = 0
    missing_ingredients = []

    print(f"\n--- {recipe_name} のコスト計算 ---")
    for ing_name, used_amount in recipes_db[recipe_name]:
        ingredient = ingredients_db.get(ing_name)
        if not ingredient:
            missing_ingredients.append(ing_name)
            continue

        unit_price = ingredient['price'] / ingredient['quantity']  # 1単位あたりの価格
        cost = unit_price * used_amount
        total_cost += cost

        print(f"{ing_name}: {used_amount}{ingredient['unit']} × {unit_price:.2f}円 = {cost:.2f}円")

    if missing_ingredients:
        print("\n⚠ 登録されていない食材があります:", ", ".join(missing_ingredients))

    print(f"\n→ 合計コスト: {total_cost:.2f}円\n")
    return total_cost



# --- 使用例 ---
register_ingredient("キャベツ", 200, 1, "個")
register_ingredient("たまねぎ", 100, 1, "個")
register_ingredient("醤油", 300, 500, "ml")

register_recipe("野菜炒め", [("キャベツ", 1), ("たまねぎ", 2), ("醤油", 15)])  # 大さじ1 = 約15ml


calculate_recipe_cost("野菜炒め")