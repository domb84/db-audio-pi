import configparser

import spotipy
import spotipy.oauth2

import os
import subprocess


class helpers ():

    def __init__(self):
        self.kill = False
        self.config_path = "db_audio_pi.conf"
        self.config = self.configparser(self.config_path)
        try:
            self.device = self.config['DEFAULT']['DEVICE']
            self.id = self.config['DEFAULT']['ID']
            self.secret = self.config['DEFAULT']['SECRET']
        except:
            print("Variables not missing from conf")

    def configparser(self, path):
        self.config = configparser.ConfigParser()
        if os.path.exists(path):
            self.config.read(path)
            for i in self.config:
                print(i)
        return self.config

    def fooFunction(self, item_index):
        """
        sample method with a parameter
        """
        print("item %d pressed" % (item_index))

    # exit sub menu
    def exitSubMenu(self, submenu):
        return submenu.exit()


    def service(self, service, action):
        try:
            if action == "start":
                return_code = subprocess.call(['sudo', 'systemctl', action, service, '--quiet'])
                return(return_code)
            elif action == "stop":
                return_code = subprocess.call(['sudo', 'systemctl', action, service, '--quiet'])
                return(return_code)
            elif action == "status":
                return_code = subprocess.call(['sudo', 'systemctl', 'is-active', '--quiet', service])
                return(return_code)
        except:
            return ("1")


    def power(self, action):
        if action == "shutdown":
            return_code = subprocess.call(['sudo', 'shutdown', '-h', 'now'])


    def spotify(self, device=None, id=None, secret=None):
        # spotify controls setup
        if not device:
            if not id:
                if not secret:
                    try:
                        self.device = self.config['DEFAULT']['DEVICE']
                        self.id = self.config['DEFAULT']['ID']
                        self.secret = self.config['DEFAULT']['SECRET']
                    except:
                        return['error']
        pi_device_id = self.device
        my_client_id = self.id
        my_client_secret = self.secret
        my_redirect_uri = 'https://example.com'
        my_scope = 'streaming user-read-currently-playing user-read-playback-state'
        refreshToken = ''
        auth = spotipy.oauth2.SpotifyOAuth(client_id=my_client_id, client_secret=my_client_secret,
                                           redirect_uri=my_redirect_uri, scope=my_scope)
        def refreshAccessToken():
            global accessTokenInfo, accessToken, spotify
            accessTokenInfo = auth.refresh_access_token(refreshToken)
            accessToken = accessTokenInfo['access_token']
            spotify = spotipy.Spotify(accessToken)

        refreshAccessToken()

        # wrapper for refreshing token - should make sure 'action' can be run partially then fully without any issues
        def spotifyAction(action, description):
            try:  # in case of failure (eg. wifi off, no song playing), don't do anything
                action()
            except Exception as e:
                print('Failed to ' + description + ': ' + str(e))
                if spotipy.oauth2.is_token_expired(accessTokenInfo):
                    refreshAccessToken()
                    spotifyAction(action, description)

        def playPauseAction():
            isOnPi = (d for d in spotify.devices()['devices'] if d['id'] == pi_device_id).next()['is_active']
            if not isOnPi:
                spotify.transfer_playback(pi_device_id)
            else:
                isPlaying = spotify.current_user_playing_track()[u'is_playing']
                spotify.pause_playback() if isPlaying else spotify.start_playback()

        playPause = lambda: spotifyAction(playPauseAction, 'play/pause')
        nextTrack = lambda: spotifyAction(spotify.next_track, 'go to next track')
        prevTrack = lambda: spotifyAction(spotify.previous_track, 'go to previous track')
        impossibleSoul = lambda: spotifyAction(seqComp(
            [lambda: spotify.start_playback(uris=['spotify:track:5CLs0uFRmU0U9VcnsI6jwv']),
             lambda: spotify.seek_track(765000), lambda: spotify.transfer_playback(pi_device_id)]), 'get hype')

