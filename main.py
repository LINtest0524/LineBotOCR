import os
import requests
import json
import re
from flask import Flask, request, abort
from deep_translator import GoogleTranslator  # ✅ 改這裡

from linebot import LineBotApi, WebhookHandler  # 若你有後續要用 SDK，可保留

# 你自己的 LINE Token 記得填
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')

LINE_REPLY_API = 'https://api.line.me/v2/bot/message/reply'

app = Flask(__name__)

# IPA ➔ KK 簡單對照表
ipa_to_kk_dict = {
    "eɪ": "e", "oʊ": "o", "aɪ": "aɪ", "aʊ": "aʊ", "ɔɪ": "ɔɪ",
    "ɪ": "ɪ", "ʊ": "ʊ", "ɛ": "ɛ", "æ": "æ", "ʌ": "ʌ",
    "ɔ": "ɔ", "ə": "ə", "i": "i", "u": "u"
}

@app.route("/")
def home():
    return "LINE Bot Server is running!"

def ipa_to_kk(ipa):
    for ipa_pattern, kk_replacement in sorted(ipa_to_kk_dict.items(), key=lambda x: -len(x[0])):
        ipa = ipa.replace(ipa_pattern, kk_replacement)
    return ipa

# 查詢字典API
def query_dictionary(word):
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word.lower()}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return None
        data = response.json()[0]
        phonetic = data.get('phonetic', '')
        audio = ''
        for p in data.get('phonetics', []):
            if 'audio' in p and p['audio']:
                audio = p['audio']
                break
        return {'phonetic': phonetic, 'audio': audio}
    except Exception as e:
        print("字典查詢錯誤：", e)
        return None

# ✅ 改這裡：用 deep-translator 進行翻譯
def translate_with_googletrans(word):
    try:
        zh = GoogleTranslator(source='en', target='zh').translate(word)
        print(f"[翻譯成功] {word} → {zh}")
        return zh
    except Exception as e:
        print(f"[翻譯錯誤] {word}：{e}")
        return word


# 建立單字字卡 (Bubble)
def build_flex_bubble(word, zh_translation, phonetic_kk, audio_url):
    bubble = {
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": f"[ {word} ]", "weight": "bold", "size": "xl", "wrap": True},
                {"type": "text", "text": zh_translation, "size": "md", "wrap": True},
                {"type": "text", "text": f"音標 (KK): {phonetic_kk}", "size": "sm", "wrap": True},
                {
                    "type": "button",
                    "style": "primary",
                    "action": {
                        "type": "uri",
                        "label": "播放",
                        "uri": audio_url if audio_url else "https://google.com"
                    }
                }
            ]
        }
    }
    return bubble

# 傳送到 LINE
def reply_message(reply_token, messages):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}'
    }
    body = json.dumps({'replyToken': reply_token, 'messages': messages})
    response = requests.post(LINE_REPLY_API, headers=headers, data=body)
    if response.status_code != 200:
        print("LINE 回應失敗:", response.status_code, response.text)

# 文字處理邏輯
def process_text(text):
    lines = text.splitlines()
    words = []
    for line in lines:
        word = line.strip()
        if re.match(r'^[a-zA-Z]+$', word):
            words.append(word)
    return list(set(words))

@app.route("/callback", methods=['POST'])
def callback():
    body = request.get_data(as_text=True)
    try:
        events = json.loads(body)['events']
        for event in events:
            if event['type'] == 'message':
                msg_type = event['message']['type']
                reply_token = event['replyToken']

                if msg_type == 'text':
                    input_text = event['message']['text']
                    words = process_text(input_text)
                    if not words:
                        reply_message(reply_token, [{"type": "text", "text": "請輸入有效單字列表"}])
                        return 'OK'

                    words = words[:10]  # 限制最多 10 個單字
                    bubbles = []
                    for word in words:
                        zh = translate_with_googletrans(word) or word
                        dict_result = query_dictionary(word)
                        if dict_result:
                            phonetic_kk = ipa_to_kk(dict_result['phonetic'])
                            bubble = build_flex_bubble(word, zh, phonetic_kk, dict_result['audio'])
                        else:
                            bubble = build_flex_bubble(word, zh, '-', '')
                        bubbles.append(bubble)

                    # Flex message 組合
                    if len(bubbles) == 1:
                        flex_msg = {
                            "type": "flex",
                            "altText": "單字翻譯",
                            "contents": bubbles[0]
                        }
                    else:
                        flex_msg = {
                            "type": "flex",
                            "altText": "單字翻譯",
                            "contents": {
                                "type": "carousel",
                                "contents": bubbles
                            }
                        }
                    reply_message(reply_token, [flex_msg])
                else:
                    reply_message(reply_token, [{"type": "text", "text": "請傳送文字單字列表！"}])
    except Exception as e:
        print("伺服器內部錯誤:", e)
        abort(400)
    return 'OK'

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)
