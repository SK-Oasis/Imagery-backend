import os

import openai
import json
from flask import Flask, redirect, render_template, request, url_for, jsonify

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
Also, tell me the main character's hp(Health Point). hp starts at 5. hp is always between 0 and 5.
Depending on my choice, hp can drop or recover.
When hp is less than or equal to 0, the main character dies and the story should be over.
Tell me the hp number first, and then tell me the story and the options.
Only When the game is over, put <END> at the end in content.
And answer in json form. 
For example, json would be like this. 
{
    "id":1,
    "hp":5,
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
The id value means the order in which you answered. And background means a description of the picture that describes the situation of the content well. And background is short description for the situation of content's story. And the background must to be written in English less than 80 characters. The theme is picture's style, and it will be used as a prompt for Dalle-2, and the Dalle-2 will have the same value as "story book, digital art" to print a prettier picture.
And the hp, content with stories, and choices with 3 options will be included in json.
And state has a value of one of playing, fail, and success. If you survive the game, you'll have success, if you die with zero stamina, you'll have fail, and the rest of playing.
background should only be written in one noun clause describing a picture that would suit the content. And, background must be written in English.  The background may vary depending on the content. Please write everything in Korean except background. state should be either fail or success at the end of the story.

Please fill out the content with up to 500 characters maximum when in English.
And according to choices, the game will be played from at least 10 questions to 100 questions. Write a story accordingly.
If the user asks a question other than the option, don't answer it, but ask them to tell you within the option.'''
    },
    {
        "role": "user",
        "content": "I want to play the game based on Apocalypse. Please describe it in detail like a novel. And when there is a change in hp, let me know with content. The background should only be written with a noun clause that describes the background and the picture that fits the user's behavior. And, background must be written in English.  The background may vary depending on the content. Please write everything in Korean except background. state should be either fail or success at the end of the story."
    },
    {
        "role": "assistant",
        "content": '''{
    "id": 1,
    "hp": 5,
    "background": "A desolate post-apocalyptic cityscape",
    "theme": "story book, digital art",
    "content": "안녕하세요! 이제부터 시작하는 모험 게임에 오신 것을 환영합니다. 이 게임은 여러분이 종말 이후의 세계에서 서바이벌과 모험을 경험하는 것을 목표로 합니다. 여러분은 황폐한 도시에서 일어난 종말의 시대에 살아남기 위해 필사적으로 노력해야 합니다. 어떻게 하시겠습니까?",
    "choices": {
        "a": "도시를 탐사한다",
        "b": "간식을 찾아다닌다",
        "c": "탈출 계획을 세운다"
    },
    "state": "playing"
}'''
    }
    ]

defaultStory = [
    {
        "role": "user",
        "content": "I want to play new game based on Apocalypse. Please describe it in detail like a novel. And when there is a change in hp, let me know with content. The background should only be written with a noun clause that describes the background and the picture that fits the user's behavior. And, background must be written in English.  The background may vary depending on the content. Please write everything in Korean except background. state should be either fail or success at the end of the story."
    }
]


messages = {
    "A":[]
    }

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
                messages = prompt + defaultStory + messages,
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
                model = "gpt-3.5-turbo-16k-0613",
                messages = prompt + defaultStory + messages,
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
    

@app.route("/api/whisper", methods=['POST'])
def get_transribe():
    print("yes")
    if 'file' not in request.files:
        return jsonify('No file part')

    file = request.files['file']

    if file:
        file.save('uploaded_file.m4a')
        print('File uploaded successfully')
    response = openai.Audio.transcribe("whisper-1", file)
    result = response["text"]
    print(result)
    return jsonify(result)


@app.route("/api/getSubject", methods=['GET'])
def api_get_subject():
    response = openai.ChatCompletion.create(
        model = "gpt-3.5-turbo-16k-0613",
        messages = [{
                        "role": "user",
                        "content": "You are a machine that creates topics randomly. Let me know a good topic to make a story randomly. For example, you can answer as follows. After the fall, zombie incidents, space travel, volcanic eruptions. Write in Korean. Less than 30 characters."
                    }],
        temperature = 1,
    )

    result = response["choices"][0]["message"]["content"]
    
    return jsonify(result)

def processOwnStory(story):
    return f"I want to play new game based on story below. {story}. Please describe it in detail like a novel. And when there is a change in hp, let me know with content. The background should only be written with a noun clause that describes the background and the picture that fits the user's behavior. And, background must be written in English.  The background may vary depending on the content. Please write everything in Korean except background. state should be either fail or success at the end of the story."

@app.route("/api/get_summary", methods=['POST'])
def get_subject_summary():
    print(request.args.get('ownStory'))
    response = openai.ChatCompletion.create(
        model = "gpt-3.5-turbo-16k-0613",
        messages = [{
                        "role": "user",
                        "content": f"Summarize the following story in one noun phrase. Please make sure that this noun phrase does not exceed 8 characters in Korean. Story : {request.args.get('ownStory')}"
                    }],
        temperature = 1,
    )

    result = response["choices"][0]["message"]["content"]
    print(result)
    return jsonify(result)


@app.route("/api/play", methods=['POST'])
def api_play():
    json_verified = False
    userId = request.args.get("userId")
    command = request.args.get("command")

    ownStory = request.args.get("ownStory")
    userId = "A"
    result = ""
    story = defaultStory

    if ownStory:
        story = [
            {
                "role": "user",
                "content" : processOwnStory(ownStory)
            }
        ]
        messages[userId] = []
    elif command:
        messages[userId].append(
            {
                "role": "user",
                "content" : command
            }
        )

    while(json_verified == False):
        try:
            response = openai.ChatCompletion.create(
                model = "gpt-3.5-turbo-16k-0613",
                messages = prompt + story + messages[userId],
                temperature = 1,
            )

            result = response["choices"][0]["message"]["content"]

            recent_data = json.loads(result)

            imageURL = openai.Image.create(
                prompt = recent_data['background'] + ', ' + recent_data['theme'],
            )["data"][0]["url"]

            data = {
                'hp' : recent_data['hp'],
                'dall' : imageURL,
                'content' : recent_data['content'],
                'state' : recent_data['state'],
                'choices' : {
                    'a' : recent_data['choices']['a'],
                    'b' : recent_data['choices']['b'],
                    'c' : recent_data['choices']['c']
                }
            }
            
            json_verified = True
        except:
            json_verified = False

    messages[userId].append(
        {
            "role": "assistant",
            "content" : result
        }
    )
    
    return jsonify(data)

@app.route("/api/reset", methods=['GET','POST'])
def api_reset():
    messages['A'] = []
    return True