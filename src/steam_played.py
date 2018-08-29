import argparse
import os
import requests
import pandas as pd
from io import BytesIO
from PIL import Image
import sys
import logging
import time
import matplotlib.pyplot as plt


def Work(args):
    """function grabs common steam user data and generates viz
    
    Arguments:
        args  -- collection of command line arguments to control settings
    """
    names = []
    minutes = []
    appid = []
    logo_url = []
    icon_url = []
    steam_img_url = 'http://media.steampowered.com/steamcommunity/public/images/apps'
    api_url =   f'http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={args.api_key}'\
            f'&include_played_free_games=1&include_appinfo=1&format=json&steamid={args.user_id}'

    # collect data from steam
    if args.new_data:
        args.logger.info('Downloading from steam api')
        req = requests.get(api_url)
        if req.status_code == 200:
            data = req.json()
            for game in data['response']['games']:
                names.append(game['name'])
                minutes.append(game['playtime_forever'])
                appid.append(game['appid'])
                icon_url.append(f"{steam_img_url}/{game['appid']}/{game['img_icon_url']}.jpg")
                logo_url.append(f"{steam_img_url}/{game['appid']}/{game['img_logo_url']}.jpg")

            df = pd.DataFrame( {   'names':names,
                                    'minutes_played':minutes,
                                    'appid':appid,
                                    'logo_url':logo_url,
                                    'icon_url':icon_url}  )
            path = os.path.join(args.out_path, f'steam_owned_{args.user_id}.csv')
            df.to_csv(path)
        else:
            args.logger.error('Could not grab data from steam api')
            sys.exit(1)
    # load previously grabbed data
    else:
        args.logger.info('Skipping steam api, loading from file')
        path = os.path.join(args.out_path, f'steam_owned_{args.user_id}.csv')
        df = pd.read_csv(path)

    # generate viz
    if args.do_viz:
        args.logger.info('Generating viz')
        df = df.sort_values(by='minutes_played', ascending=False)
        urls = df['logo_url'].iloc[:args.n_games]
        output = Image.new('RGB', (args.out_width, args.out_height))
        for index, item in enumerate(urls):
            pic_req = requests.get(item)
            if pic_req.status_code == 200:
                im = Image.open(BytesIO(pic_req.content))
                output.paste(im, ((index%args.n_cols)*args.width + 10,(index//args.n_cols)*args.height + 20))
            else:
                args.logger.warning(f'problem getting: {pic_req}')
            time.sleep(args.nice_time)
        path = os.path.join(args.out_path, f'steam_top{args.n_games}_{args.user_id}.png')
        output.save(path)

        if args.bars > 0:
            args.logger.info('Generating bar chart')
            df['hours_played'] = df['minutes_played'] / 60
            plt.style.use('seaborn')
            fig, ax = plt.subplots()
            df = df.iloc[:args.bars]
            # force barchart to go in reverse minute order
            plt.barh(range(len(df), 0, -1), df['hours_played'])
            plt.yticks(range(len(df), 0, -1), df['names'])
            ax.set(title='Most Played Steam Games', xlabel='hours')
            path = os.path.join(args.out_path, f'steam_bar{args.bars}_{args.user_id}.png')
            plt.tight_layout()
            plt.savefig(path)


if __name__ == '__main__':
    """ script that uses steam api to collect public user info and store in a csv,
        can also product visualizations based on this data
    """
    parser = argparse.ArgumentParser(description='Collects top games from steam public user')
    parser.add_argument('api_key', help='Devs steam API key')
    parser.add_argument('user_id', help='Public steam users id')
    parser.add_argument('-r', '--rows', dest='n_rows', type=int, default=5, help='Number of rows')
    parser.add_argument('-c', '--cols', dest='n_cols', type=int, default=5, help='Number of cols')
    parser.add_argument('-w', '--width', dest='width', type=int, default=200, help='Width of individual pic')
    parser.add_argument('-t', '--tall', dest='height', type=int, default=100, help='Height of individual pic')
    parser.add_argument('-b', '--bar', dest='bars', type=int, default=15, help='Number of bars to draw')
    parser.add_argument('-v', '--viz', dest='do_viz', action='store_false', help='Specify if you dont want a viz')
    parser.add_argument('-d', '--data', dest='new_data', action='store_false', help='Specify if the data exists already')
    args = parser.parse_args()

    # add extra useful stuff
    args.n_games = args.n_rows * args.n_cols
    args.out_width = args.n_cols * args.width
    args.out_height = args.n_rows * args.height
    args.out_path = '../out/'
    args.log_path = '../log/'
    args.nice_time = 5

    # logging base to include everything
    args.logger = logging.getLogger(__name__)
    args.logger.setLevel(logging.DEBUG)
    # only warnings or higher to file
    path = os.path.join(args.log_path, 'error.log')
    fh = logging.FileHandler(path)
    fh.setLevel(logging.WARNING)
    args.logger.addHandler(fh)
    # info and higher to screen
    sh = logging.StreamHandler()
    sh.setLevel(logging.INFO)
    args.logger.addHandler(sh)

    path = os.path.join(args.log_path, 'run.log')
    with open(path, 'a') as f:
        arg_str = ' '.join(sys.argv)
        sep = '-' * 80
        out_str = f'{arg_str}\n{sep}\n'
        f.write(out_str)

    Work(args)
