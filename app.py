import os

import openai
import json
from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__)
openai.api_key = os.getenv("OPENAI_API_KEY")


prompt=[
    {
        "role": "system",
        "content": '''You are a scriptwriter for an adventure game.
At the beginning of the story, I want you to explain the background at least 300 characters in detail.
Please write a first-person game scenario, and always gives me 3 options the main character can do.
Please talk from a first-person perspective instead of using the expression "game" to make the user feel immersed.
And I hope there's a conversation with other characters.
And I want you to proceed with the story according to my choice.
Also, tell me the main character's HP(Health Point). HP starts at 5. HP is always between 0 and 5.
Depending on my choice, HP can drop or recover.
When HP drops below zero, the main character dies and the game is over.
Tell me the HP number first, and then tell me the story and the options.
Only When the game is over, put <END> at the end in content.
And answer in json form. 
For example, json would be like this. 
{
    "ID":1,
    "HP":5,
    "background": "The hero who appeared as a warrior in a fantasy world full of magic and monsters",
    "theme":"story book, digital art",
    "content":"안녕하세요! 이제부터 시작하는 모험 게임에 오신 것을 환영합니다. 이 게임은 여러분이 영웅이 되어 다양한 도전과 과제를 수행하는 것을 목표로 합니다. 게임 세계는 마법과 몬스터로 가득 찬 판타지 세계입니다. 여러분의 할일은 영웅의 역할을 맡아 세계를 구하는 것입니다. 어떻게 하시겠습니까?",
    "choices":
    {
        "a":"모험을 시작한다!",
        "b":"게임 규칙을 알려주세요.",
        "c":"이 게임은 어떻게 진행되나요?"
    },
    "state":"playing"
}
The ID value means the order in which you answered. And background means a description of the picture that describes the situation of the content well. And background is short description for the situation of content's story. And the background have to be written in English less than 80 characters. The theme is picture's style, and it will be used as a prompt for Dalle-2, and the Dalle-2 will have the same value as "story book, digital art" to print a prettier picture.
And the HP, content with stories, and choices with 3 options will be included in json.
And state has a value of one of playing, fail, and success. If you survive the game, you'll have success, if you die with zero stamina, you'll have fail, and the rest of playing.

Please fill out the content with up to 500 characters maximum when in English.
And according to choices, the game will be played from at least 10 questions to 100 questions. Write a story accordingly.
If the user asks a question other than the option, don't answer it, but ask them to tell you within the option.'''
    },
    {
        "role": "user",
        "content": "I want to play the game based on Apocalypse. (background 는 영어로 써주고 그를 제외한 모든 내용은 한국어로 작성해줘.)"
    },
    {
        "role": "assistant",
        "content": '''{
    "ID":1,
    "HP":5,
    "background": "The hero who appeared as a warrior in a fantasy world full of magic and monsters",
    "theme":"story book, digital art",
    "content":"안녕하세요! 이제부터 시작하는 모험 게임에 오신 것을 환영합니다. 이 게임은 여러분이 영웅이 되어 다양한 도전과 과제를 수행하는 것을 목표로 합니다. 게임 세계는 마법과 몬스터로 가득 찬 판타지 세계입니다. 여러분의 할일은 영웅의 역할을 맡아 세계를 구하는 것입니다. 어떻게 하시겠습니까?",
    "choices":
    {
        "a":"모험을 시작한다!",
        "b":"게임 규칙을 알려주세요.",
        "c":"이 게임은 어떻게 진행되나요?"
    },
    "state":"playing"
}'''
    },
    {
        "role": "user",
        "content": "I want to play new game based on Apocalypse. 게임을 클리어할 수 있도록 난이도를 약간만 쉽게 해주고. 소설처럼 자세히 묘사해줘. 그리고 체력에 변동이 있을 때에 content 내용으로 알려줘 (background 는 영어로 써주고 그를 제외한 모든 내용은 한국어로 작성해줘.)"
    }
    ]

messages = []

def summarize(openai: any, messages: list) -> str:
    content = ''''''
    for message in messages:
        content += message["content"]+'\n'
    print("CONTENT________", content)
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{
            'role': 'user',
            'content': f'다음 내용들을 두 세줄로 요약해줘. ###\n{content}\n###'
        }],
        temperature = 1,
    )

    return completion.choices[0].message.content


@app.route("/", methods=(["GET"]))
def index():
    return render_template("index.html")

@app.route("/command", methods=(["POST"]))
def command():
    if request.method == "POST":
        type = request.form["type"]
        if type == "Submit":
            command = request.form["command"]
            messages.append(
                {
                    "role": "user",
                    "content" : command
                }
            )
            #TODOS : https://github.com/openai/openai-cookbook/blob/main/examples/How_to_stream_completions.ipynb
            response = openai.ChatCompletion.create(
                model = "gpt-3.5-turbo-0613",
                messages = prompt + messages,
                temperature = 1,
                #stream=True
            )

            if (response["usage"]["total_tokens"] > 3500):
                print(messages)
                summarized = summarize(openai, messages)
                print(summarized)

            result = response["choices"][0]["message"]["content"]

            messages.append(
                {
                    "role": "assistant",
                    "content" : result
                }
            )

            results = []
            for message in messages:
                if message["role"] == "assistant":
                    results.append({"role": message["role"], "content" : json.loads(message["content"])})
                elif message["role"] == "user":
                    results.append({"role": message["role"], "content" : message["content"]})

            return render_template("index.html", results=results)#redirect(url_for("index", results=results))#render_template("index.html", results=results)
        else:
            response = openai.ChatCompletion.create(
                model = "gpt-3.5-turbo-0613",
                messages = prompt + messages,
                temperature = 1,
            )

            result = response["choices"][0]["message"]["content"]
            
            messages.append(
                {
                    "role": "assistant",
                    "content" : result
                }
            )
            results = []
            for message in messages:
                if message["role"] == "assistant":
                    results.append({"role": message["role"], "content" : json.loads(message["content"])})
                elif message["role"] == "user":
                    results.append({"role": message["role"], "content" : message["content"]})

            return render_template("index.html", results=results)#redirect(url_for("index", results=results))#render_template("index.html", results=results)
    


@app.route("/hello", methods=['GET'])
def hello():
  a = {"body" : "data",
       "title" :"text"}
  return json.loads(a)