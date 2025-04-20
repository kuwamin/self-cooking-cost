import tkinter as tk
from tkinter import messagebox
import json
import os
from tkinter import ttk
import pykakasi
kks = pykakasi.kakasi()


# データベースの定義 ------------------------------------------------------------------------------------------------------------------------------------------------------
ingredients_db = {}
recipes_db = {}

ING_FILE = "ingredients.json"
REC_FILE = "recipes.json"


# データベースの保存と読み込み ------------------------------------------------------------------------------------------------------------------------------------------------------
def save_ingredients():
    with open(ING_FILE, "w", encoding="utf-8") as f:
        json.dump(ingredients_db, f, ensure_ascii=False, indent=2)

def load_ingredients():
    global ingredients_db
    if os.path.exists(ING_FILE):
        with open(ING_FILE, "r", encoding="utf-8") as f:
            ingredients_db = json.load(f)

def save_recipes():
    with open(REC_FILE, "w", encoding="utf-8") as f:
        json.dump(recipes_db, f, ensure_ascii=False, indent=2)

def load_recipes():
    global recipes_db
    if os.path.exists(REC_FILE):
        with open(REC_FILE, "r", encoding="utf-8") as f:
            recipes_db = json.load(f)


# メモ情報 ------------------------------------------------------------------------------------------------------------------------------------------------------
MEMO_TEXT = (
    "💡 使用量の参考メモ：\n"
    "・大さじ1 = 約15ml\n"
    "・小さじ1 = 約5ml\n"
    "・1カップ = 約200ml\n"
)


# 50音順に並び変える関数 ------------------------------------------------------------------------------------------------------------------------------------------------------
def get_hiragana_reading(text):
    result = kks.convert(text)
    return ''.join([item['hira'] for item in result])


# 食材登録に関する関数群 ------------------------------------------------------------------------------------------------------------------------------------------------------

# 食材を登録する関数 ----------------------------------------------------------------------
def register_ingredient():
    name = name_entry.get()
    price = price_entry.get()
    quantity = quantity_entry.get()
    unit = unit_entry.get()

    try:
        price = float(price)
        quantity = float(quantity)
    except ValueError:
        messagebox.showerror("入力エラー", "価格と数量は数値で入力してください。")
        return

    if not name or not unit:
        messagebox.showerror("入力エラー", "すべての項目を入力してください。")
        return

    ingredients_db[name] = {
        'price': price,
        'quantity': quantity,
        'unit': unit
    }

    save_ingredients()
    update_ingredient_list()
    clear_ingredient_inputs()
    messagebox.showinfo("登録完了", f"{name} を登録しました。")


# 食材の入力を消去する関数 ----------------------------------------------------------------------
def clear_ingredient_inputs():
    name_entry.delete(0, tk.END)
    price_entry.delete(0, tk.END)
    quantity_entry.delete(0, tk.END)
    unit_entry.delete(0, tk.END)


# 食材リストを更新する関数 ----------------------------------------------------------------------
def update_ingredient_list():
    listbox.delete(0, tk.END)

    # 読み仮名をキーにしてソート
    sorted_names = sorted(ingredients_db.keys(), key=get_hiragana_reading)

    for name in sorted_names:
        info = ingredients_db[name]
        listbox.insert(tk.END, f"{name}: {info['price']}円 / {info['quantity']}{info['unit']}")

    recipe_ing_name_entry['values'] = sorted_names


# 選択した食材の情報をロードする関数 ----------------------------------------------------------------------
def load_selected_ingredient():
    selection = listbox.curselection()
    if not selection:
        return
    selected_text = listbox.get(selection[0])
    name = selected_text.split(":")[0]

    data = ingredients_db.get(name)
    if not data:
        return

    name_entry.delete(0, tk.END)
    name_entry.insert(0, name)
    price_entry.delete(0, tk.END)
    price_entry.insert(0, str(data['price']))
    quantity_entry.delete(0, tk.END)
    quantity_entry.insert(0, str(data['quantity']))
    unit_entry.delete(0, tk.END)
    unit_entry.insert(0, data['unit'])


# 食材の情報を更新する関数 ----------------------------------------------------------------------
def update_ingredient():
    name = name_entry.get()
    price = price_entry.get()
    quantity = quantity_entry.get()
    unit = unit_entry.get()

    if name not in ingredients_db:
        messagebox.showerror("エラー", f"{name} はまだ登録されていません。")
        return

    try:
        price = float(price)
        quantity = float(quantity)
    except ValueError:
        messagebox.showerror("入力エラー", "価格と数量は数値で入力してください。")
        return

    ingredients_db[name] = {
        'price': price,
        'quantity': quantity,
        'unit': unit
    }

    save_ingredients()
    update_ingredient_list()
    clear_ingredient_inputs()
    messagebox.showinfo("更新完了", f"{name} を更新しました。")


# 食材の情報を削除する関数 ----------------------------------------------------------------------
def remove_ingredient():
    selection = listbox.curselection()
    if not selection:
        messagebox.showwarning("選択エラー", "削除したい食材を選択してください。")
        return

    selected_text = listbox.get(selection[0])
    name = selected_text.split(":")[0]

    confirm = messagebox.askyesno("確認", f"{name} を削除しますか？")
    if not confirm:
        return

    if name in ingredients_db:
        del ingredients_db[name]
        save_ingredients()
        update_ingredient_list()
        clear_ingredient_inputs()
        messagebox.showinfo("削除完了", f"{name} を削除しました。")

        

# 料理登録に関する関数群 ------------------------------------------------------------------------------------------------------------------------------------------------------
current_ingredients = []

# 料理（レシピ）に食材を追加する関数 ----------------------------------------------------------------------
def add_ingredient_to_recipe():
    ing_name = recipe_ing_name_entry.get()
    ing_amount = recipe_ing_amount_entry.get()

    if ing_name not in ingredients_db:
        messagebox.showerror("エラー", f"食材「{ing_name}」は未登録です。")
        return

    try:
        ing_amount = float(ing_amount)
    except ValueError:
        messagebox.showerror("入力エラー", "使用量は数値で入力してください。")
        return

    current_ingredients.append((ing_name, ing_amount))
    update_current_recipe_list()
    recipe_ing_name_entry.delete(0, tk.END)
    recipe_ing_amount_entry.delete(0, tk.END)


# 選択した食材に合わせて使用量の単位を更新する関数 ----------------------------------------------------------------------
def update_unit_display(event=None):
    ing_name = recipe_ing_name_entry.get()
    unit = ingredients_db.get(ing_name, {}).get("unit", "")
    unit_display_label.config(text=unit)


# 料理を更新する関数 ----------------------------------------------------------------------
def update_current_recipe_list():
    recipe_listbox.delete(0, tk.END)
    for ing_name, amount in current_ingredients:
        unit = ingredients_db.get(ing_name, {}).get("unit", "")
        recipe_listbox.insert(tk.END, f"{ing_name}: {amount}{unit}")


# 料理を登録する関数 ----------------------------------------------------------------------
def register_recipe():
    recipe_name = recipe_name_entry.get()
    if not recipe_name:
        messagebox.showerror("エラー", "料理名を入力してください。")
        return

    if not current_ingredients:
        messagebox.showerror("エラー", "食材が1つも登録されていません。")
        return

    try:
        servings = int(recipe_servings_entry.get())
    except ValueError:
        servings = 1  # 未入力や不正値なら1食分とする

    recipes_db[recipe_name] = {
        "ingredients": current_ingredients.copy(),
        "servings": servings
}

    save_recipes()
    update_recipe_list()
    current_ingredients.clear()
    update_current_recipe_list()
    recipe_name_entry.delete(0, tk.END)
    messagebox.showinfo("登録完了", f"{recipe_name} を登録しました。")

    cost_text = calculate_recipe_cost_text(recipe_name)
    cost_label.config(text=cost_text)


# レシピのデータベースを更新する関数 ----------------------------------------------------------------------
def update_recipe_list():
    recipe_listbox_all.delete(0, tk.END)

    # 料理名を50音順にソート（漢字・ひらがな・カタカナ混在でもOK）
    sorted_recipes = sorted(recipes_db.items(), key=lambda item: get_hiragana_reading(item[0]))

    for recipe, data in sorted_recipes:
        if isinstance(data, dict):
            items = data.get("ingredients", [])
            servings = data.get("servings", 1)
        else:
            items = data
            servings = 1

        total_cost = 0
        for ing_name, amount in items:
            info = ingredients_db.get(ing_name)
            if info:
                unit_price = info['price'] / info['quantity']
                total_cost += unit_price * amount

        recipe_listbox_all.insert(
            tk.END, f"{recipe}（合計{total_cost:.0f}円／{servings}食）"
        )


# 選択した料理の情報をロードする関数 ----------------------------------------------------------------------
def load_selected_recipe():
    selection = recipe_listbox_all.curselection()
    if not selection:
        return

    selected_text = recipe_listbox_all.get(selection[0])
    recipe_name = selected_text.split("（")[0].strip()

    data = recipes_db.get(recipe_name)
    if not data:
        return

    # データが辞書（新形式）かリスト（旧形式）かを判定
    if isinstance(data, dict):
        items = data.get("ingredients", [])
        servings = data.get("servings", 1)
    else:
        items = data
        servings = 1

    # フォームに反映
    recipe_name_entry.delete(0, tk.END)
    recipe_name_entry.insert(0, recipe_name)

    recipe_servings_entry.delete(0, tk.END)
    recipe_servings_entry.insert(0, str(servings))

    current_ingredients.clear()
    for ing in items:
        current_ingredients.append(ing)  # ing は (名前, 量) のタプル

    update_current_recipe_list()

    cost_text = calculate_recipe_cost_text(recipe_name)
    cost_label.config(text=cost_text)


# 料理を更新する関数 ----------------------------------------------------------------------
def update_recipe():
    recipe_name = recipe_name_entry.get()
    if recipe_name not in recipes_db:
        messagebox.showerror("エラー", f"{recipe_name} は登録されていません。")
        return

    if not current_ingredients:
        messagebox.showerror("エラー", "食材が1つも登録されていません。")
        return

    recipes_db[recipe_name] = current_ingredients.copy()
    save_recipes()
    update_recipe_list()
    current_ingredients.clear()
    update_current_recipe_list()
    recipe_name_entry.delete(0, tk.END)
    messagebox.showinfo("更新完了", f"{recipe_name} を更新しました。")


# 
def load_selected_ingredient_in_recipe():
    selection = recipe_listbox.curselection()
    if not selection:
        return
    ing_name, amount = current_ingredients[selection[0]]
    recipe_ing_name_entry.delete(0, tk.END)
    recipe_ing_name_entry.insert(0, ing_name)
    recipe_ing_amount_entry.delete(0, tk.END)
    recipe_ing_amount_entry.insert(0, str(amount))


# レシピから食材を消去する関数 ----------------------------------------------------------------------
def remove_ingredient_from_recipe():
    selection = recipe_listbox.curselection()
    if not selection:
        messagebox.showwarning("選択エラー", "削除したい食材を選択してください。")
        return
    del current_ingredients[selection[0]]
    update_current_recipe_list()


# レシピを削除する関数 ----------------------------------------------------------------------
def remove_selected_recipe():
    selection = recipe_listbox_all.curselection()
    if not selection:
        messagebox.showwarning("選択エラー", "削除したい料理を選択してください。")
        return

    selected_text = recipe_listbox_all.get(selection[0])
    recipe_name = selected_text.split("（")[0].strip()

    confirm = messagebox.askyesno("確認", f"{recipe_name} を削除しますか？")
    if not confirm:
        return

    if recipe_name in recipes_db:
        del recipes_db[recipe_name]
        save_recipes()
        update_recipe_list()
        cost_label.config(text="ここにコストが表示されます")
        messagebox.showinfo("削除完了", f"{recipe_name} を削除しました。")


# レシピのコストを計算する関数 ----------------------------------------------------------------------
def calculate_recipe_cost_text(recipe_name):
    data = recipes_db.get(recipe_name)
    if isinstance(data, dict):
        items = data.get("ingredients", [])
        servings = data.get("servings", 1)
    else:
        items = data
        servings = 1

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

    # 合計と1食あたりを表示
    details.append(f"\n合計コスト: {total_cost:.2f}円")
    if servings > 0:
        per_serving = total_cost / servings
        details.append(f"（1食あたり: {per_serving:.2f}円）")

    return "\n".join(details)



# GUI ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------
root = tk.Tk()
root.title("食材＆料理登録アプリ")

# 食材登録フレーム ----------------------------------------------------------------------------------------------------------------------------------------------------------------
frame_ingredient = tk.LabelFrame(root, text="【食材登録】", padx=10, pady=10)
frame_ingredient.grid(row=0, column=0, padx=10, pady=10, sticky='n')

tk.Label(frame_ingredient, text="食材名").grid(row=0, column=0, sticky='w')
name_entry = tk.Entry(frame_ingredient, width=20)
name_entry.grid(row=0, column=1)

tk.Label(frame_ingredient, text="価格（円）").grid(row=1, column=0, sticky='w')
price_entry = tk.Entry(frame_ingredient, width=20)
price_entry.grid(row=1, column=1)

tk.Label(frame_ingredient, text="購入量").grid(row=2, column=0, sticky='w')
quantity_entry = tk.Entry(frame_ingredient, width=20)
quantity_entry.grid(row=2, column=1)

tk.Label(frame_ingredient, text="単位").grid(row=3, column=0, sticky='w')
unit_entry = tk.Entry(frame_ingredient, width=20)
unit_entry.grid(row=3, column=1)

tk.Button(frame_ingredient, text="食材登録", command=register_ingredient, width=20).grid(row=4, column=0, columnspan=2, pady=5)
ingredient_scrollbar = tk.Scrollbar(frame_ingredient)
ingredient_scrollbar.grid(row=5, column=2, sticky='ns')

listbox = tk.Listbox(frame_ingredient, width=40, height=6, yscrollcommand=ingredient_scrollbar.set)
listbox.grid(row=5, column=0, columnspan=2)

ingredient_scrollbar.config(command=listbox.yview)


listbox.bind('<<ListboxSelect>>', lambda event: load_selected_ingredient())

tk.Button(frame_ingredient, text="更新", command=update_ingredient, width=20).grid(row=6, column=0, columnspan=2, pady=5)

tk.Button(frame_ingredient, text="選択した食材を削除", command=remove_ingredient, width=20).grid(row=7, column=0, columnspan=2, pady=5)




# 料理登録フレーム -------------------------------------------------------------------------------------------------------------------------------------------------------------------
frame_recipe = tk.LabelFrame(root, text="【料理登録】", padx=10, pady=10)
frame_recipe.grid(row=0, column=1, padx=10, pady=10, sticky='n')

tk.Label(frame_recipe, text="料理名").grid(row=0, column=0, sticky='w')
recipe_name_entry = tk.Entry(frame_recipe, width=20)
recipe_name_entry.grid(row=0, column=1)

tk.Label(frame_recipe, text="食材名").grid(row=1, column=0, sticky='w')
recipe_ing_name_entry = ttk.Combobox(frame_recipe, width=18, state='readonly')
recipe_ing_name_entry.grid(row=1, column=1)

recipe_ing_name_entry.bind("<<ComboboxSelected>>", update_unit_display)

tk.Label(frame_recipe, text="使用量").grid(row=2, column=0, sticky='w')
recipe_ing_amount_entry = tk.Entry(frame_recipe, width=20)
recipe_ing_amount_entry.grid(row=2, column=1)

unit_display_label = tk.Label(frame_recipe, text="", width=6, anchor='w')
unit_display_label.grid(row=2, column=2, sticky='w')

tk.Label(frame_recipe, text="食数").grid(row=3, column=0, sticky='w')
recipe_servings_entry = tk.Entry(frame_recipe, width=20)
recipe_servings_entry.grid(row=3, column=1)

tk.Button(frame_recipe, text="食材を追加", command=add_ingredient_to_recipe, width=20).grid(row=4, column=0, columnspan=2, pady=5)
recipe_scrollbar = tk.Scrollbar(frame_recipe)
recipe_scrollbar.grid(row=5, column=2, sticky='ns')

recipe_listbox = tk.Listbox(frame_recipe, width=40, height=6, yscrollcommand=recipe_scrollbar.set)
recipe_listbox.grid(row=5, column=0, columnspan=2)

recipe_scrollbar.config(command=recipe_listbox.yview)

tk.Button(frame_recipe, text="選択した食材を削除", command=remove_ingredient_from_recipe, width=20).grid(row=6, column=0, columnspan=2, pady=2)


# 登録済み料理 + コスト計算 ------------------------------------------------------------------------------------------------------------------------------------------------------------------
frame_result = tk.LabelFrame(root, text="【料理一覧】", padx=10, pady=10)
frame_result.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky='ew')

result_scrollbar = tk.Scrollbar(frame_result)
result_scrollbar.grid(row=0, column=2, sticky='ns')

recipe_listbox_all = tk.Listbox(frame_result, width=80, height=4, yscrollcommand=result_scrollbar.set)
recipe_listbox_all.grid(row=0, column=0, columnspan=2)

result_scrollbar.config(command=recipe_listbox_all.yview)


cost_label = tk.Label(frame_result, text="ここにコストが表示されます", justify='left', anchor='w')
cost_label.grid(row=2, column=0, columnspan=2, sticky='w')



recipe_listbox_all.bind('<<ListboxSelect>>', lambda event: load_selected_recipe())

recipe_listbox.bind("<<ListboxSelect>>", lambda e: load_selected_ingredient_in_recipe())

tk.Button(frame_recipe, text="料理を登録/更新", command=register_recipe, width=20).grid(row=7, column=0, columnspan=2, pady=5)

tk.Button(frame_result, text="選択した料理を削除", command=remove_selected_recipe).grid(row=3, column=0, columnspan=2, pady=5)



# メモ-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
memo_label = tk.Label(root, text=MEMO_TEXT, justify='left', anchor='w', fg='gray')
memo_label.grid(row=2, column=0, columnspan=2, padx=10, sticky='w')


# データ読み込みと初期表示 ----------------------------------------------------------------------------------------------------------------------------------------------------------------------
load_ingredients()
load_recipes()
update_ingredient_list()
update_recipe_list()

root.mainloop()
