import flet as ft
import os
from linebot import LineBotApi
from linebot.models import TextSendMessage
from linebot.exceptions import LineBotApiError

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

# LINEのチャンネルアクセストークン
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
# LINEのユーザーID
LINE_USER_ID = os.environ.get('LINE_USER_ID')

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
        self.page.fonts = {
            "Corporate-Logo-Rounded": "/fonts/Corporate-Logo-Rounded-Bold-ver3.otf"
        }
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

        # 注文履歴格納用辞書
        self.order_history_dict = {}

        # LINEメッセージ送信用
        self.line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN) if LINE_CHANNEL_ACCESS_TOKEN is not None else None
        self.line_bot_userid = LINE_USER_ID

    # 注文履歴をアップデート
    def order_dict_update(self, order_name: str, order_count: int):
        if order_name in self.order_history_dict:
            self.order_history_dict[order_name] = self.order_history_dict[order_name] + order_count
        else:
            self.order_history_dict[order_name] = order_count

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
        print("「{}」を{}個注文しました.".format(self.order_name, self.order_count))
        # 注文履歴を更新
        self.order_dict_update(self.order_name, self.order_count)

        # LINE用のトークンが設定されている場合
        if self.line_bot_api is not None and self.line_bot_userid is not None:
            try:
                self.line_bot_api.push_message(self.line_bot_userid, TextSendMessage(text="「{}」が{}個注文されました.".format(self.order_name, self.order_count)))
            except LineBotApiError as e:
                print("->LINE送信エラー (注文に失敗しました)")

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
                            content=ft.ElevatedButton("いいえ", icon=ft.icons.CANCEL, color="white", bgcolor="red", on_click=self.modal_close),
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

        # LINE用のトークンが設定されている場合
        if self.line_bot_api is not None and self.line_bot_userid is not None:
            try:
                self.line_bot_api.push_message(self.line_bot_userid, TextSendMessage(text="店員呼び出し中..\nテーブルへ向かってください."))
            except LineBotApiError as e:
                print("->LINE送信エラー (店員呼び出しに失敗しました)")

        self.page.update()

    # お会計リクエスト (はい押下時)
    def bill_request(self, e):
        # モーダルダイアログを閉じる
        self.dlg_modal.open = False

        print("お会計を行いました.")

        if len(self.order_history_dict) == 0:
            order_text = "\n注文商品はありません"
        else:
            order_text = ""
            for one_order_name in self.order_history_dict:
                order_text = order_text + "\n{}:{}個".format(one_order_name, self.order_history_dict[one_order_name])

        print("お会計が行われました.{}".format(order_text))

        # LINE用のトークンが設定されている場合
        if self.line_bot_api is not None and self.line_bot_userid is not None:
            try:
                self.line_bot_api.push_message(self.line_bot_userid, TextSendMessage(text="お会計が行われました.{}".format(order_text)))
            except LineBotApiError as e:
                print("->LINE送信エラー (お会計に失敗しました)")

        # 注文履歴をクリア
        self.order_history_dict = {}

        self.page.update()

    # モーダルウィンドウ閉じる (閉じる・いいえ押下時)
    def modal_close(self, e):
        # モーダルダイアログを閉じる
        self.dlg_modal.open = False

        self.page.update()


    # モーダルダイアログを開く (注文一覧ダイアログ)
    def check_order_history_dlg_modal(self, e):

        # 選択時のモーダルダイアログ
        self.dlg_modal = ft.AlertDialog(
            title=ft.Text("注文一覧"),
            # content=ft.TextButton("閉じる", icon=ft.icons.CANCEL, icon_color="red400", on_click=self.modal_close),
            actions=[
                #* わかりにくいがリスト内包表記でリストを展開して返している
                ft.Row(
                    [
                        ft.Container(
                            content=ft.Text(value=one_order_name, size=15, weight=ft.FontWeight.W_900),
                            margin=ft.margin.only(top=1, bottom=4),
                            # padding=10,
                            alignment=ft.alignment.center_left
                        ),

                        ft.Container(
                            content=ft.Text(value=str(self.order_history_dict[one_order_name]) + "個", size=15, weight=ft.FontWeight.W_900),
                            margin=ft.margin.only(top=1, bottom=4),
                            # padding=10,
                            alignment=ft.alignment.center_right
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                )
                for one_order_name in self.order_history_dict
            ],
            # on_dismiss=lambda e: print("Modal dialog dismissed!"),
        )

        self.page.dialog = self.dlg_modal

        if len(self.dlg_modal.actions) == 0:
            self.dlg_modal.actions.append(ft.Row([ft.Container(content=ft.Text("注文した商品はありません"), margin=ft.margin.only(top=1, bottom=4))], alignment=ft.MainAxisAlignment.CENTER))
        self.dlg_modal.actions.append(ft.Row([ft.TextButton("閉じる", icon=ft.icons.CANCEL, icon_color="red400", on_click=self.modal_close)], alignment=ft.MainAxisAlignment.CENTER))
        self.dlg_modal.open = True
        self.page.update()

    # モーダルダイアログを開く (お会計ダイアログ)
    def bill_dlg_modal(self, e):
        # 選択時のモーダルダイアログ
        self.dlg_modal = ft.AlertDialog(
            modal=True,
            title=ft.Text("お会計"),
            content=ft.Text("お会計を行いますか?", text_align=ft.TextAlign.CENTER),
            actions=[
                ft.Row(
                    [
                        ft.Container(
                            content=ft.ElevatedButton(" は い ", icon=ft.icons.CHECK_CIRCLE_SHARP, color="white", bgcolor="blue", on_click=self.bill_request),
                            margin=ft.margin.only(top=10),  # 上方向のみマージンを入れる
                            # padding=10,
                            alignment=ft.alignment.center_left
                        ),

                        ft.Container(
                            content=ft.ElevatedButton("いいえ", icon=ft.icons.CANCEL, color="white", bgcolor="red", on_click=self.modal_close),
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

    ## ロゴ
    logo_text_field = ft.Row([
        ft.Image(src=f"/images/logo.png", width=80, height=47, fit=ft.ImageFit.FILL, repeat=ft.ImageRepeat.NO_REPEAT, border_radius=ft.border_radius.all(10)),
        ft.Text("お寿司注文", size=50, weight=ft.FontWeight.NORMAL, color="#F36890", font_family="Corporate-Logo-Rounded"),
        ft.Text("アプリ", size=50, weight=ft.FontWeight.NORMAL, color="#86CCFD", font_family="Corporate-Logo-Rounded")
        ],
        spacing=0
        )

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
                    on_click=flet_app.bill_dlg_modal,
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
                    on_click=flet_app.check_order_history_dlg_modal,
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
                    icon=ft.icons.FORMAT_LIST_BULLETED_ROUNDED,
                ),
                margin=ft.margin.only(top=25, bottom=25, right=10, left=10),
            ),
        ]
    )

    flet_app.page.add(
        logo_text_field,
        tab_field,
        function_button_field
    )

if __name__ == "__main__":

    # GUIアプリとして起動
    # ft.app(
    #     target=main,
    #     assets_dir="assets"
    # )

    # WEBブラウザで起動
    ft.app(
        target=main,
        view=ft.WEB_BROWSER,
        port=8550,
        assets_dir="assets"
    )