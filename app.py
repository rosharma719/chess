from flask import Flask, request, redirect, url_for, session, render_template, flash, jsonify
from gameLogic import *
from bot import botMove, checkMove
import logging
import random
import os
import dotenv
import json

config = json.load(open("config.json"))
dotenv.load_dotenv()

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.getenv('SECRET_KEY')  # Use a real key in production
logging.basicConfig(level=logging.DEBUG)

@app.route('/', methods=['GET'])
def index():
    logging.debug("Index called")
    session['botWhite'] = random.choice([True, False])
    session['board'] = newBoard(session['botWhite'])
    session['gameStates'] = [session['board']]
    session['turn'] = 'bot' if session['botWhite'] else 'player'
    session['promote'] = False

    logging.debug(f"New game started with botWhite: {session['botWhite']}")

    if session['turn'] == 'bot':
        logging.debug("Bot starts, making the first move.")
        new_board = botMove(session['board'], session['turn'], session['gameStates'], session['botWhite'])
        if new_board:
            session['board'] = new_board
            session['gameStates'].append(new_board)
            session['turn'] = 'player'
            logging.debug("Bot made the first move, switching to player.")

    return redirect(url_for('active'))

@app.route('/active', methods=['GET'])
def active():
    logging.debug("Active page called")
    return render_template('index.html', board=session['board'], turn=session['turn'], promote=session['promote'], botWhite=session['botWhite'])

@app.route('/make_move', methods=['POST'])
def make_move():
    logging.debug("Make move called")
    response = {}
    move_input = request.json.get('move')
    if move_input:
        validity, piece, dest = inputValidate(move_input, session['board'], session['botWhite'], session['turn'], session['gameStates'])
        if validity == "castle":
            session['board'] = castle(session['turn'], session['board'], session['botWhite'])
            session['gameStates'].append(session['board'])
            session['turn'] = 'bot'
            response['status'] = 'castle'
        elif validity:
            session['board'] = movePiece(piece, dest, session['board'], session['gameStates'], session['turn'])
            session['gameStates'].append(session['board'])

            if piece.lower().startswith('p') and (dest // 8 == 0 or dest // 8 == 7):
                session['promote'] = True
                session['promotion_piece'] = piece
                session['promotion_dest'] = dest
                response['status'] = 'promote'
            else:
                status = checkCheckmateOrStalemate(session['board'], 'player', session['botWhite'], session['gameStates'])
                if status == 'checkmate':
                    response['status'] = 'checkmate'
                    response['winner'] = 'player' if session['turn'] == 'player' else 'bot'
                elif status == 'stalemate':
                    response['status'] = 'stalemate'
                else:
                    session['turn'] = 'bot'
                    response['status'] = 'success'
        else:
            response['status'] = 'invalid'

    response['board'] = session['board']
    response['turn'] = session['turn']
    response['promote'] = session['promote']
    response['botWhite'] = session['botWhite']
    return jsonify(response)

@app.route('/bot_move', methods=['POST'])
def bot_move():
    logging.debug("Bot Move called")
    response = {}
    if session['turn'] == 'bot':
        if not isKingSafe(session['board'], session['turn']):
            new_board = checkMove(session['board'], session['turn'], session['gameStates'], session['botWhite'])
        else:
            new_board = botMove(session['board'], session['turn'], session['gameStates'], session['botWhite'])
        
        if new_board:
            print("Board exists")
            if isKingSafe(new_board, session['turn']):
                print("King is safe")
                session['board'] = new_board
                session['gameStates'].append(new_board)
                status = checkCheckmateOrStalemate(session['board'], 'bot', session['botWhite'], session['gameStates'])
                if status == 'checkmate':
                    response['status'] = 'checkmate'
                    response['winner'] = 'bot'
                elif status == 'stalemate':
                    response['status'] = 'stalemate'
                else:
                    session['turn'] = 'player'
                    response['status'] = 'success'
        else:
            print("HELP")
            response['status'] = 'error'

    response['board'] = session['board']
    response['turn'] = session['turn']
    response['botWhite'] = session['botWhite']
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=config["debugMode"])
