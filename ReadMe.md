# Tic Tac Toe

## Installation guide
1. Open the Terminal
2. Install python3.12
3. Install redis <br> 
MacOS: brew install redis  <br> 
Linux: sudo apt install redis <br> 
4. MacOS: brew services start redis <br> 
Linux: sudo systemctl start redis 
5. git clone https://github.com/Rock-Lex/TicTacToe-Web.git 
6. python3.12  -m venv .venv 
7. source .venv/bin/activate (on Linux/MacOS) 
8. pip install –r requirements.txt 
9. Create .env Datei 
In .env 3 Lines schreiben: <br> 
DJANGO_SECRET_KEY='django-insecure-wjvy$j&$y-90l0ztt$(x6bstoc1wgd1jxc7#7w-gzi+)*d6^ll' <br> 
DEBUG=True <br>
DEVELOPMENT_MODE=True <br> 
10. cd tictactoe/apps/frontend 
11. npm install 
12. npm run dev (laufen lassen) 
13. Open new terminal tab (You need to be in the root-dir of the project) <br> 
14. cd tictactoe 
15. python manage.py makemigrations 
16. python manage.py migrate 
17. python manage.py runserver 8000 