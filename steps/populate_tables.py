from bs4 import BeautifulSoup
from requests import get
import os
import re
import sexmachine.detector as sexmachine
import sqlite3 as sql


def populate_tables():

    MAX_GAME_ID = 4786
    # MAX_PLAYER_ID = 9268

    database_path = os.path.abspath('archive.db')

    con = sql.connect(database_path)
    cur = con.cursor()

    gender_detector = sexmachine.Detector()

    for game_id in xrange(4113, MAX_GAME_ID + 1):

        print 'Parsing game ' + str(game_id) + '...',

        game_url = ('http://www.j-archive.com/showgame.php?game_id=' +
                    str(game_id))

        r = get(game_url)
        if r.status_code != 200:
            print 'Error in game ' + str(game_id)
            continue

        soup = BeautifulSoup(r.text)

        try:
            double_rows = (soup.find(id='double_jeopardy_round')
                           .find_all('table')[-1]
                           .find_all('tr'))
            double_scores_tds = double_rows[1].find_all('td')

            final_rows = (soup.find(id='final_jeopardy_round')
                          .find_all('table')[-1]
                          .find_all('tr'))
            final_scores_tds = final_rows[1].find_all('td')
        except:
            continue

        comments = soup.find(id='game_comments').text
        date = soup.title.text[-10:]

        cur.execute('INSERT INTO Games (Id, Date, Comments) '
                    'VALUES (?, ?, ?)', (game_id, date, comments,))

        player_els = soup.find_all('p', class_='contestants')
        for player_score_index, player_el in enumerate(player_els):

            player_link = player_el.find('a')
            player_name = player_link.text
            player_gender = gender_detector.get_gender(player_name.split()[0])
            player_id = re.sub(r'\D', '', player_link['href'])

            cur.execute('INSERT OR IGNORE INTO Players (Id, Name, Gender) '
                        'VALUES (?, ?, ?)', (
                            player_id,
                            player_name,
                            player_gender,
                        ))

            wagered_score = re.sub(r'\D', '',
                                   double_scores_tds[player_score_index].text)
            coryat_score = re.sub(r'\D', '',
                                  final_scores_tds[player_score_index].text)

            cur.execute('INSERT INTO Scores '
                        '(Game_Id, Player_Id, Wagered_Score, Coryat_Score) '
                        'VALUES (?, ?, ?, ?)', (
                            game_id,
                            player_id,
                            wagered_score,
                            coryat_score,
                        ))

        con.commit()
        print 'parsed.'

    con.close()

if __name__ == '__main__':
    populate_tables()
