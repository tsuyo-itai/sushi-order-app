import flet as ft
import json
from http import HTTPStatus
import requests
import os
import sys
# 画像はここからいいのが取れそう
# https://japaclip.com/sushi/


NigiriImagePathDict = {
    "マグロ": f"/images/sushi-tuna.png",
    "えび": f"/images/sushi-shrimp.png",
    "いか": f"/images/sushi-squid.png",
    "たこ": f"/images/sushi-octopus.png",
    "ブリ": f"/images/sushi-buri.png",
    "たまご": f"/images/sushi-egg.png",
    "ホタテ": f"/images/sushi-hotate.png",
    "サーモン": f"/images/sushi-salmon.png",

}

GunkanImagePathDict = {
    "いくら": f"/images/sushi-salmon-roe.png",
    "ねぎとろ": f"/images/sushi-negitoro.png",
    "ウニ": f"/images/sushi-sea-urchin.png",
    "納豆巻き": f"/images/sushi-natto.png",
    "コーン": f"/images/sushi-corn.png",
    "巻き寿司": f"/images/norimaki.png"
}

SidemenuImagePathDict = {
    "アンパン": f"/images/anpan.png"
}

# 画面内に表示する横の列の最大画像(寿司)数
MAX_ROW_VIEW_IMAGE_NUM = 4

# 注文時に実行するAPI
ORDER_API = os.environ.get('ORDER_API')
# 店員呼び出し時に実行するAPI
CLERK_CALL_API = os.environ.get('CLERK_CALL_API')

# リスト取得関数 (list index out of range回避)
def list_get(lst, index, error):
    return lst[index] if len(lst) > index else error

# リストをN分割する関数
#! 基本 make_list_from_split_list() 内からコールする
def split_list(l, n):
    for i in range(0, len(l), n):
        yield l[i:i+n]

# N分割したリストをリスト化する関数
def make_list_from_split_list(l, n):
    return list(split_list(l, n))


# 辞書のValueからKeyを取得する関数
def getdictkey_from_value(dic, value):
    for k,v in dic.items():
        if v == value:
            #該当するkeyに何らかの操作を実行
            return k
    else:
        # 辞書にvalueが存在しない場合はNoneを返す
        return None




class FletApp(object):
    def __init__(self, page):
        self.page = page
        self.page.title = "お寿司注文.app"
        ## 縦中央揃え
        # page.vertical_alignment = ft.MainAxisAlignment.CENTER
        ## 横中央揃え
        self.page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

        # 横列表示用の寿司画像配列　(2次元)
        self.NigiriImageArray = self.create_image_array(NigiriImagePathDict)
        self.GunkanImageArray = self.create_image_array(GunkanImagePathDict)
        self.SidemenuImageArray = self.create_image_array(SidemenuImagePathDict)


        # 注文数
        self.order_count = 1
        # 注文品名
        self.order_name = None

    # 描画用の寿司画像配列の作成 2次元リストとなる
    def create_image_array(self, target_array):
        # 寿司画像配列
        sushi_image_array = []
        for sushi_image_key in target_array:
            image_field = ft.Image(
                src=target_array[sushi_image_key],
                width=200,
                height=150,
                fit=ft.ImageFit.FILL,
                repeat=ft.ImageRepeat.NO_REPEAT,
                border_radius=ft.border_radius.all(10),
            )

            sushi_image_array.append(image_field)

        # リストを表示横画像数で分割する
        sushi_image_array = make_list_from_split_list(sushi_image_array, MAX_ROW_VIEW_IMAGE_NUM)

        return sushi_image_array

    # fletの画像表示View要素作成 (コンテナ要素内にイメージ要素を入れたもの)
    def create_row_image_field(self, input_array, target_array):
        if input_array is None:
            # リスト要素取得に失敗した場合はNoneを返す (list index out of range)
            return None
        else:
            #* わかりにくいがリスト内包表記でリストを展開して返している
            return [
                ft.Container(
                    content=sushi_image,
                    margin=ft.margin.only(top=10, left=25, right=25),
                    padding=10,
                    alignment=ft.alignment.center,
                    width=250,
                    height=200,
                    border_radius=10,
                    ink=True,
                    on_click=self.order_dlg_modal,
                    data=getdictkey_from_value(target_array, sushi_image.src)
                )
                for sushi_image in input_array
            ]

    # モーダルダイアログを開く (注文確認ダイアログ)
    def order_dlg_modal(self, e):
        # 注文ダイアログ表示時にカウントクリアする
        self.order_count = 1
        # 注文品名保持用へ代入
        self.order_name = e.control.data
        #* テキストフィールド内は注文数変動により値を変更するため、変数化する(アクションへ変数を渡したいから) 他にいい方法ないかな..
        order_count_text_field = ft.Text(value=str(self.order_count), size=30, weight=ft.FontWeight.W_900)
        # 選択時のモーダルダイアログ
        self.dlg_modal = ft.AlertDialog(
            modal=True,
            title=ft.Text(self.order_name),  # Containerで設定したdata値が入る
            content=ft.Text("注文を確定する場合は「注文」を選択してください."),
            actions=[
                ft.Row(
                    [
                        ft.IconButton(ft.icons.REMOVE, on_click=self.order_mainus_click, data=order_count_text_field),
                        order_count_text_field,
                        ft.IconButton(ft.icons.ADD, on_click=self.order_plus_click, data=order_count_text_field),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.Row(
                    [
                        ft.Container(
                            content=ft.ElevatedButton("　注文　", icon=ft.icons.ADD_SHOPPING_CART, color="white", bgcolor="blue", on_click=self.order_request),
                            margin=ft.margin.only(top=25),  # 上方向のみマージンを入れる
                            # padding=10,
                            alignment=ft.alignment.center_left
                        ),

                        ft.Container(
                            content=ft.ElevatedButton("取り消し", icon=ft.icons.CANCEL, color="white", bgcolor="red", on_click=self.order_cancel),
                            margin=ft.margin.only(top=25),  # 上方向のみマージンを入れる
                            # padding=10,
                            alignment=ft.alignment.center_right
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.END,
                )

            ],
            on_dismiss=lambda e: print("Modal dialog dismissed!"),
        )

        self.page.dialog = self.dlg_modal
        self.dlg_modal.open = True
        self.page.update()

    # 注文リクエスト (注文押下時)
    def order_request(self, e):
        # モーダルダイアログを閉じる
        self.dlg_modal.open = False
        print("{}を{}個注文しました.".format(self.order_name, self.order_count))
        if ORDER_API is not None:
            # APIが環境変数で設定されていれば実行
            body_message = {'sushi_name': self.order_name, 'sushi_num': self.order_count}
            print("post request:{}".format(ORDER_API))
            res = requests.post(ORDER_API, data=json.dumps(body_message))
            if res.status_code == HTTPStatus.OK:
                # 成功
                print("status_code:{} response:{}".format(res.status_code, res.json()))
            else:
                # パラメータ異常
                # その他異常 (Internal server error 含む)
                print("status_code:{} response:{}".format(res.status_code, res.json()))

        # 念の為注文数クリア
        self.order_count = 1
        # 念の為注文品名クリア
        self.order_name = None

        self.page.update()

    # 注文キャンセル (取り消し押下時)
    def order_cancel(self, e):
        # モーダルダイアログを閉じる
        self.dlg_modal.open = False
        # 念の為注文数クリア
        self.order_count = 1
        # 念の為注文品名クリア
        self.order_name = None

        self.page.update()

    # 数量「＋」を押下したときのイベント
    def order_plus_click(self, e):
        # MAX注文数を99までとする
        if self.order_count < 99:
            self.order_count += 1
        else:
            pass
        # テキストフィールドのvalue値を加算
        e.control.data.value = str(self.order_count)

        self.page.update()

    # 数量「-」を押下したときのイベント
    def order_mainus_click(self, e):
        # 最小注文数を1とする
        if self.order_count <= 1:
            pass
        else:
            self.order_count -= 1
        # テキストフィールドのvalue値を加算
        e.control.data.value = str(self.order_count)

        self.page.update()


    # モーダルダイアログを開く (店員呼び出しダイアログ)
    def clerk_call_dlg_modal(self, e):

        # 選択時のモーダルダイアログ
        self.dlg_modal = ft.AlertDialog(
            modal=True,
            title=ft.Text("店員呼び出し"),
            content=ft.Text("店員の呼び出しを行いますか?", text_align=ft.TextAlign.CENTER),
            actions=[
                ft.Row(
                    [
                        ft.Container(
                            content=ft.ElevatedButton(" は い ", icon=ft.icons.CHECK_CIRCLE_SHARP, color="white", bgcolor="blue", on_click=self.clerk_call_request),
                            margin=ft.margin.only(top=10),  # 上方向のみマージンを入れる
                            # padding=10,
                            alignment=ft.alignment.center_left
                        ),

                        ft.Container(
                            content=ft.ElevatedButton("いいえ", icon=ft.icons.CANCEL, color="white", bgcolor="red", on_click=self.clerk_call_cancel),
                            margin=ft.margin.only(top=10),  # 上方向のみマージンを入れる
                            # padding=10,
                            alignment=ft.alignment.center_right
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                )

            ],
            on_dismiss=lambda e: print("Modal dialog dismissed!"),
        )

        self.page.dialog = self.dlg_modal
        self.dlg_modal.open = True
        self.page.update()

    # 店員呼び出しリクエスト (はい押下時)
    def clerk_call_request(self, e):
        # モーダルダイアログを閉じる
        self.dlg_modal.open = False

        print("店員を呼び出しました")
        if CLERK_CALL_API is not None:
            # APIが環境変数で設定されていれば実行
            body_message = {'message_kind': "CLERK_CALL_API"}
            print("post request:{}".format(CLERK_CALL_API))
            res = requests.post(CLERK_CALL_API, data=json.dumps(body_message))
            if res.status_code == HTTPStatus.OK:
                # 成功
                print("status_code:{} response:{}".format(res.status_code, res.json()))
            else:
                # パラメータ異常
                # その他異常 (Internal server error 含む)
                print("status_code:{} response:{}".format(res.status_code, res.json()))

        self.page.update()

    # 店員呼び出しキャンセル (いいえ押下時)
    def clerk_call_cancel(self, e):
        # モーダルダイアログを閉じる
        self.dlg_modal.open = False

        self.page.update()

def main(page: ft.Page):
    flet_app = FletApp(page)

    ###* にぎり
    ## 1段目列
    nigiri_first_row_field = ft.Row(
        flet_app.create_row_image_field(list_get(flet_app.NigiriImageArray, 0, None), NigiriImagePathDict)
    )

    ## 2段目列
    nigiri_second_row_field = ft.Row(
        flet_app.create_row_image_field(list_get(flet_app.NigiriImageArray, 1, None), NigiriImagePathDict)
    )

    ## 3段目列
    nigiri_third_row_field = ft.Row(
        flet_app.create_row_image_field(list_get(flet_app.NigiriImageArray, 2, None), NigiriImagePathDict)
    )

    ###* 軍艦
    ## 1段目列
    gunkan_first_row_field = ft.Row(
        flet_app.create_row_image_field(list_get(flet_app.GunkanImageArray, 0, None), GunkanImagePathDict)
    )

    ## 2段目列
    gunkan_second_row_field = ft.Row(
        flet_app.create_row_image_field(list_get(flet_app.GunkanImageArray, 1, None), GunkanImagePathDict)
    )

    ## 3段目列
    gunkan_third_row_field = ft.Row(
        flet_app.create_row_image_field(list_get(flet_app.GunkanImageArray, 2, None), GunkanImagePathDict)
    )

    ###* サイドメニュー
    ## 1段目列
    sidemenu_first_row_field = ft.Row(
        flet_app.create_row_image_field(list_get(flet_app.SidemenuImageArray, 0, None), SidemenuImagePathDict)
    )

    ## 2段目列
    sidemenu_second_row_field = ft.Row(
        flet_app.create_row_image_field(list_get(flet_app.SidemenuImageArray, 1, None), SidemenuImagePathDict)
    )

    ## 3段目列
    sidemenu_third_row_field = ft.Row(
        flet_app.create_row_image_field(list_get(flet_app.SidemenuImageArray, 2, None), SidemenuImagePathDict)
    )

    # #! list index out of rangeの場合Noneが返るが、ft.Row(None)であれば描画されないので問題なしとする


    ## タブ 1 にぎり
    tab_field = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        tabs=[
            ft.Tab(
                text="にぎり",
                icon=ft.icons.LOOKS_ONE_ROUNDED,
                # Column(縦) に対してRow(横)要素3つ入れている
                content=ft.Column([
                    nigiri_first_row_field,
                    nigiri_second_row_field,
                    nigiri_third_row_field
                ])
            ),
            ft.Tab(
                text="軍艦",
                icon=ft.icons.LOOKS_TWO_ROUNDED,
                # Column(縦) に対してRow(横)要素3つ入れている
                content=ft.Column([
                    gunkan_first_row_field,
                    gunkan_second_row_field,
                    gunkan_third_row_field
                ])
            ),
            ft.Tab(
                text="サイド・メニュー",
                icon=ft.icons.LOOKS_3_ROUNDED,
                # Column(縦) に対してRow(横)要素3つ入れている
                content=ft.Column([
                    sidemenu_first_row_field,
                    sidemenu_second_row_field,
                    sidemenu_third_row_field
                ])
            ),
        ],
        expand=1,
    )

    ## 機能ボタン要素 (最下層)
    function_button_field = ft.Row(
        [
            ft.Container(
                content = ft.OutlinedButton(
                    "店員呼び出し",
                    on_click=flet_app.clerk_call_dlg_modal,
                    style=ft.ButtonStyle(
                        color={
                            ft.MaterialState.HOVERED: ft.colors.WHITE,
                            ft.MaterialState.FOCUSED: ft.colors.WHITE,
                            ft.MaterialState.DEFAULT: ft.colors.WHITE70,
                        },
                        bgcolor={ft.MaterialState.FOCUSED: ft.colors.WHITE, "": ft.colors.RED},
                        shape=ft.RoundedRectangleBorder(radius=5),
                        padding=18
                    ),
                    icon=ft.icons.EMOJI_PEOPLE
                ),
                margin=ft.margin.only(top=25, bottom=25, right=10, left=10),
            ),
            ft.Container(
                content = ft.OutlinedButton(
                    "　　お会計　　",
                    style=ft.ButtonStyle(
                        color={
                            ft.MaterialState.HOVERED: ft.colors.WHITE,
                            ft.MaterialState.FOCUSED: ft.colors.WHITE,
                            ft.MaterialState.DEFAULT: ft.colors.WHITE70,
                        },
                        bgcolor={ft.MaterialState.FOCUSED: ft.colors.WHITE, "": ft.colors.BLUE},
                        shape=ft.RoundedRectangleBorder(radius=5),
                        padding=18
                    ),
                    icon=ft.icons.ATTACH_MONEY_ROUNDED
                ),
                margin=ft.margin.only(top=25, bottom=25, right=10, left=10),
            ),

            ft.Container(
                content = ft.OutlinedButton(
                    " 　注文一覧　 ",
                    style=ft.ButtonStyle(
                        color={
                            ft.MaterialState.HOVERED: ft.colors.WHITE,
                            ft.MaterialState.FOCUSED: ft.colors.WHITE,
                            ft.MaterialState.DEFAULT: ft.colors.WHITE70,
                        },
                        bgcolor={ft.MaterialState.FOCUSED: ft.colors.WHITE, "": ft.colors.GREEN},
                        shape=ft.RoundedRectangleBorder(radius=5),
                        padding=18
                    ),
                    icon=ft.icons.ADD_SHOPPING_CART,
                ),
                margin=ft.margin.only(top=25, bottom=25, right=10, left=10),
            ),
        ]
    )

    flet_app.page.add(
        tab_field,
        function_button_field
    )

if __name__ == "__main__":

    # ft.app(
    #     target=main,
    #     assets_dir="assets"
    # )

    ft.app(
        target=main,
        view=ft.WEB_BROWSER,
        port=8550,
        assets_dir="assets"
    )