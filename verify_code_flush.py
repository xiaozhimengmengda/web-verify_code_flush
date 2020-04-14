import random
import string
import uuid
import base64
import platform
from PIL import Image, ImageDraw,ImageFont
from io import BytesIO
from sanic import Sanic
from sanic.response import HTTPResponse,text, json
from sanic.views import HTTPMethodView

app = Sanic()

session = {}


class VerifyCode:
    def __init__(self, numbers:int):
        """
        指定:生成的数量
        """
        self.number = numbers

    def draw_lines(self, draw, width, height):
        """划线"""

        x1 = random.randint(0, width / 2)
        y1 = random.randint(0, height / 2)
        x2 = random.randint(0, width)
        y2 = random.randint(height / 2, height)
        draw.line(((x1, y1), (x2, y2)), fill='black', width=1)

    def random_color(self):
        """随机颜色"""
        return random.randint(32, 127), random.randint(32, 127), random.randint(32, 127)

    def gene_text(self):
        """生成验证码"""
        return "".join(random.sample(string.ascii_letters+string.digits, self.number))

    def get_verify_code(self):
        """
        draw.text()：
            文字的绘制，第一个参数指定绘制的起始点（文本的左上角所在位置），第二个参数指定文本内容，第三个参数指定文本的颜色，第四个参数指定字体（通过ImageFont类来定义）
        """
        code = self.gene_text()
        width, height = 130, 30
        im = Image.new("RGB", (width, height), "white")
        # 这里指定字体的路径
        sysstr = platform.system()
        font = None
        if sysstr == "Windows":
            font = ImageFont.truetype("C:\WINDOWS\Fonts\STXINGKA.TTF", 25)
        elif sysstr == "Darwin":
            font = ImageFont.truetype('/Library/Fonts/AppleMyungjo.ttf', 25)
        draw = ImageDraw.Draw(im)
        for item in range(self.number):
            draw.text((5+random.randint(-5, 5)+23*item, 5+random.randint(-5, 5)), text=code[item],
                      fill=self.random_color(), font=font)
            self.draw_lines(draw, width, height)
        return im, code


class SimpleView(HTTPMethodView):
    body = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>马哥教育公开课</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@3.3.7/dist/css/bootstrap.min.css" integrity="sha384-BVYiiSIFeK1dGmJRAkycuHAHRg32OmUcww7on3RYdg4Va+PmSTsz/K68vbdEjh4u" crossorigin="anonymous">
    <!-- 可选的 Bootstrap 主题文件（一般不用引入） -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@3.3.7/dist/css/bootstrap-theme.min.css" integrity="sha384-rHyoN1iRsVXV4nD0JutlnGaslCJuC7uwjduW9SVrLvRYooPp2bWYgmgJQIXwl/Sp" crossorigin="anonymous">
    <!-- 最新的 Bootstrap 核心 JavaScript 文件 -->
    <script src="http://ajax.aspnetcdn.com/ajax/jQuery/jquery-1.9.1.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@3.3.7/dist/js/bootstrap.min.js" integrity="sha384-Tc5IQib027qvyjSMfHjOMaLkfuWVxZxUPnCJA7l2mCWNIpG9mGCD8wGNIcPD7Txa" crossorigin="anonymous"></script>
</head>
<body>
<form class="form-inline" method="post" action="">
    <div>
         <div class="form-group">
                {error}                               
        </div>
        <div class="form-group">
            <label for="exampleInputName2">验证码</label>
           <input type="text" class="form-control" id="captcha" name="code">
        </div>
        <div class="form-group">
            <img src="data:image/jpeg;base64,{base64_data}" class="img-img-rounded" id="img">
        </div>
        <div class="form-group">
            <button type="submit" id="submit">验证</button>
        </div>
    </div>
</form>
</body>
<script type="text/javascript">
jQuery(document).ready(function(){{
    $("#img").click(function(){{
        $.post("",
        {{
            type:"put"
        }},
        function(data){{
            var image = data["result"]["base64_data"]
            var arr=new Array();
            arr.push("data:image/jpeg;base64,")
            arr.push(image)
            var h = arr.join("")
            $("#img").attr("src", h);
        }});
    }});
}});
</script>
</html>
    """

    async def get(self, request):
        return self.response(id="", error="")

    async def post(self, request):
        uuid = request.cookies.get("uuid", "")
        method = request.form.get("type", "")
        if method:
            base64_data = self.put(request)
            return json({"status": "success", "result": {"base64_data": base64_data}})
        verfy_code = request.form.get("code", "2").lower()
        code = session.get(uuid, "").lower()
        if code == verfy_code:
            return text('验证码正确')
        return self.response(id=uuid, error='<input class="form-control" id="disabledInput" type="text" placeholder="验证码错误" disabled>')

    def put(self, request):
        uuid = request.cookies.get("uuid", "")
        base64_data, code = self.code()
        session[uuid] = code
        return base64_data

    def code(self):
        im, code = VerifyCode(5).get_verify_code()
        buf = BytesIO()
        im.save(buf, "jpeg")
        buf_str = buf.getvalue()
        base64_data = base64.b64encode(buf_str).decode()
        print(code)
        return base64_data, code

    def response(self, id, error):
        id = id if id else uuid.uuid1().__str__()
        base64_data, code = self.code()
        session[id] = code
        body = self.body.format(base64_data=base64_data, error=error)
        response = HTTPResponse(body, content_type="text/html; charset=utf-8")
        response.cookies["uuid"] = id
        return response


app.add_route(SimpleView.as_view(), '')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
