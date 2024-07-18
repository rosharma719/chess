from flask import Flask, request, redirect, url_for, session, render_template, flash
from gameLogic import *
from bot import botMove
import logging
import random

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = 'your_secret_key'  # Use a real key in production

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

@app.route('/active', methods=['GET', 'POST'])
def active():
    logging.debug("Active page called")

    if request.method == 'POST':
        if 'promotion_piece' in request.form:
            piece = session['promotion_piece']
            dest = session['promotion_dest']
            new_piece = request.form['promotion_piece']
            session['board'] = promotePawn(piece, dest, new_piece, session['board'])
            session['gameStates'].append(session['board'])
            session['turn'] = 'bot'
            session['promote'] = False
            logging.debug("Pawn promoted, bot's turn next.")
            return redirect(url_for('move'))

        move_input = request.form.get('move')
        if move_input:
            validity, piece, dest = inputValidate(move_input, session['board'], session['botWhite'], session['turn'], session['gameStates'])
            if validity == "castle":
                session['board'] = castle(session['turn'], session['board'], session['botWhite'])
                session['gameStates'].append(session['board'])
                session['turn'] = 'bot'
                logging.debug("Player castled successfully, bot's turn next.")
                return redirect(url_for('move'))
            elif validity:
                session['board'] = movePiece(piece, dest, session['board'], session['gameStates'], session['turn'])
                session['gameStates'].append(session['board'])

                if piece.lower().startswith('p') and (dest // 8 == 0 or dest // 8 == 7):
                    session['promote'] = True
                    session['promotion_piece'] = piece
                    session['promotion_dest'] = dest
                    return redirect(url_for('active'))

                session['turn'] = 'bot'
                logging.debug("Player moved successfully, bot's turn next.")
                return redirect(url_for('move'))
            else:
                flash('Invalid move!', 'error')

    return render_template('index.html', board=session['board'], turn=session['turn'], promote=session['promote'])

@app.route('/move', methods=['GET'])
def move():
    logging.debug("Bot Move called")
    if session['turn'] == 'bot':
        new_board = botMove(session['board'], session['turn'], session['gameStates'], session['botWhite'])
        if new_board:
            session['board'] = new_board
            session['gameStates'].append(new_board)
            session['turn'] = 'player'
            logging.debug("Bot made a move, switching to player")
        else:
            logging.error("Bot failed to make a valid move")
            flash('Bot failed to make a move.', 'error')

    return redirect(url_for('active'))

if __name__ == '__main__':
    app.run(debug=False)
