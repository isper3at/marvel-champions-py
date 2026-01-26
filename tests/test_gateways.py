"""Tests for gateway implementations"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
from src.entities.deck import DeckList
from src.gateways import LocalImageStorage, MarvelCDBClient
from src.config import ImageStorageConfig, MarvelCDBConfig


class TestLocalImageStorage:
    """Test LocalImageStorage"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory"""
        temp = tempfile.mkdtemp()
        yield temp
        shutil.rmtree(temp)
    
    @pytest.fixture
    def storage_config(self, temp_dir):
        """Create storage config"""
        return ImageStorageConfig(
            storage_path=temp_dir,
            max_image_size=5 * 1024 * 1024
        )
    
    def test_save_and_get_image(self, storage_config):
        """Test saving and retrieving image"""
        storage = LocalImageStorage(storage_config)
        
        image_data = b'fake image data'
        path = storage.save_image('01001a', image_data)
        
        assert path is not None
        assert storage.image_exists('01001a') is True
        
        retrieved_path = storage.get_image_path('01001a')
        assert retrieved_path == path
        
        # Verify file was actually created
        assert Path(path).exists()
        with open(path, 'rb') as f:
            assert f.read() == image_data
    
    def test_image_not_exists(self, storage_config):
        """Test checking non-existent image"""
        storage = LocalImageStorage(storage_config)
        
        assert storage.image_exists('nonexistent') is False
        assert storage.get_image_path('nonexistent') is None
    
    def test_delete_image(self, storage_config):
        """Test deleting image"""
        storage = LocalImageStorage(storage_config)
        
        storage.save_image('01001a', b'fake data')
        assert storage.image_exists('01001a') is True
        
        deleted = storage.delete_image('01001a')
        assert deleted is True
        assert storage.image_exists('01001a') is False
    
    def test_delete_nonexistent_image(self, storage_config):
        """Test deleting image that doesn't exist"""
        storage = LocalImageStorage(storage_config)
        
        deleted = storage.delete_image('nonexistent')
        assert deleted is False
    
    def test_get_all_image_codes(self, storage_config):
        """Test listing all stored images"""
        storage = LocalImageStorage(storage_config)
        
        storage.save_image('01001a', b'data1')
        storage.save_image('01002a', b'data2')
        storage.save_image('01003a', b'data3')
        
        codes = storage.get_all_image_codes()
        assert len(codes) == 3
        assert '01001a' in codes
        assert '01002a' in codes
        assert '01003a' in codes
    
    def test_image_size_limit(self, storage_config):
        """Test image size limit"""
        storage = LocalImageStorage(storage_config)
        
        # Create data larger than limit (5MB)
        large_data = b'x' * (6 * 1024 * 1024)
        
        with pytest.raises(ValueError, match="exceeds maximum"):
            storage.save_image('large', large_data)
    
    def test_sanitize_card_code_with_slash(self, storage_config):
        """Test that card codes with slashes are sanitized"""
        storage = LocalImageStorage(storage_config)
        
        # Card code with slash (some MarvelCDB cards have this)
        storage.save_image('01001a/b', b'data')
        assert storage.image_exists('01001a/b') is True
        
        # Check that file doesn't actually have slash
        path = storage.get_image_path('01001a/b')
        assert '/' not in Path(path).name
    
    def test_save_overwrites_existing(self, storage_config):
        """Test that saving overwrites existing image"""
        storage = LocalImageStorage(storage_config)
        
        storage.save_image('01001a', b'old data')
        path1 = storage.get_image_path('01001a')
        
        storage.save_image('01001a', b'new data')
        path2 = storage.get_image_path('01001a')
        
        # Should be same path
        assert path1 == path2
        
        # Should have new data
        with open(path2, 'rb') as f:
            assert f.read() == b'new data'
    
    def test_supports_png_and_jpg(self, storage_config):
        """Test that storage supports both PNG and JPG"""
        storage = LocalImageStorage(storage_config)
        
        # Save as jpg (default)
        path_jpg = storage.save_image('card1', b'jpg data')
        assert path_jpg.endswith('.jpg')
        
        # Manually create a PNG file
        png_path = Path(storage_config.storage_path) / 'card2.png'
        png_path.write_bytes(b'png data')
        
        # Should find PNG
        assert storage.image_exists('card2') is True
        found_path = storage.get_image_path('card2')
        assert found_path.endswith('.png')


class TestMarvelCDBClient:
    """Test MarvelCDBClient gateway"""
    
    @pytest.fixture
    def config(self):
        """Create MarvelCDB config"""
        return MarvelCDBConfig(
            base_url='https://marvelcdb.com',
            rate_limit_calls=10,
            rate_limit_period=60,
            request_delay=0.1
        )
    
    @pytest.fixture
    def client(self, config):
        """Create client"""
        return MarvelCDBClient(config)
    
    def test_rate_limiting(self, client):
        """Test that rate limiting delays requests"""
        import time
        
        # Mock the actual request
        with patch.object(client.session, 'get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.content = b'<html></html>'
            
            start = time.time()
            
            # Make two requests
            client._rate_limit()
            client._rate_limit()
            
            elapsed = time.time() - start
            
            # Should have delayed at least request_delay seconds
            assert elapsed >= client.config.request_delay
    
    @patch('requests.Session.get')
    def test_get_card_info_success(self, mock_get, client):
        """Test successful card info retrieval"""
        # Mock HTML response
        html = '''
        <html>
            <h1 class="card-name">Spider-Man</h1>
            <div class="card-text">Response ability text</div>
        </html>
        '''
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = html.encode()
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        result = client.get_card_from_code('01001a')

        assert result.code == '01001a'
        assert result.name == 'Spider-Man'
        assert 'Response ability' in result.text
    
    @patch('requests.Session.get')
    def test_get_card_info_failure(self, mock_get, client):
        """Test card info retrieval failure"""
        mock_get.side_effect = Exception("Network error")
        
        with pytest.raises(Exception, match="Network error"):
            client.get_card_from_code('01001a')
    
    @patch('requests.Session.get')
    def test_get_card_image_url(self, mock_get, client):
        """Test getting card image URL"""
        html = '''
        <html>
            <img class="card-image" src="//example.com/card.jpg" />
        </html>
        '''
        local_image_store = Mock()
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = html.encode()
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        assert client.get_card_image('01001a', local_image_store)
    
    @patch('requests.Session.get')
    def test_get_card_image_url_relative(self, mock_get, client):
        """Test getting card image with relative URL"""
        html = '''
        <html>
            <img class="card-image" src="/images/card.jpg" />
        </html>
        '''
        local_image_store = Mock()
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = html.encode()
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        assert client.get_card_image('01001a', local_image_store)
    
    @patch('requests.Session.get')
    def test_download_card_image_failure(self, mock_get, client):
        """Test card image download failure"""
        mock_get.side_effect = Exception("Network error")
        
        with pytest.raises(Exception):
            client.download_card_image('https://example.com/card.png')
    
    @patch('requests.Session.get')
    def test_get_user_decks(self, mock_get, client):
        """Test getting user's deck list"""
        html = '''
        <html><plasmo-csui id="jobright-helper-plugin"></plasmo-csui><head>
    <title>House of Pain · MarvelCDB</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="mobile-web-app-capable" content="yes">
    <link rel="icon" sizes="192x192" href="/icon-192.png">
    <link rel="apple-touch-icon" sizes="120x120" href="/icon-120.png">
        
    <link href="https://fonts.googleapis.com/css?family=Amiri:400,400italic,700,700italic|Julius+Sans+One|Open+Sans:400,400italic,700,700italic|Open+Sans+Condensed:300" rel="stylesheet" type="text/css">
		<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.4.0/css/font-awesome.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/qtip2/2.1.1/jquery.qtip.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap-markdown/2.9.0/css/bootstrap-markdown.min.css">
        <link rel="stylesheet" href="/css/app.css">
		<!--[if lt IE 9]>
      <script src="//cdnjs.cloudflare.com/ajax/libs/html5shiv/3.7/html5shiv.js"></script>
      <script src="//cdnjs.cloudflare.com/ajax/libs/respond.js/1.4.2/respond.js"></script>
    <![endif]-->
	  </head>
  <body>
  <div id="wrapper">
      <nav class="navbar navbar-default navbar-static-top" role="navigation">
      <div class="container">
                  <div class="navbar-header">
          <button type="button" class="navbar-toggle" data-toggle="collapse" data-target=".navbar-collapse">
            <span class="icon-bar"></span>
            <span class="icon-bar"></span>
            <span class="icon-bar"></span>
          </button>
          <a class="navbar-brand" href="/">
            <span class="icon icon-link-half-top"></span>
            <span class="icon icon-link-half-bottom"></span>
            MarvelCDB
          </a>
        </div>
        <div class="navbar-collapse collapse">
          <ul class="nav navbar-nav">
            <li><a href="/decks">My Decks</a></li>
            <li><a href="/decklists">Decklists</a></li>
            <li><a href="/search">Cards</a></li>
            <li class="hidden-sm"><a href="/reviews">Reviews</a></li>
            <li class="hidden-sm"><a href="/rules">Rules</a></li>
            <li class="hidden-sm"><a href="/faqs">FAQs</a></li>
          </ul>
          <ul class="nav navbar-nav navbar-right">
            <li class="dropdown hidden-xs hidden-lg">
              <a href="#" class="dropdown-toggle" data-toggle="dropdown" role="button" aria-expanded="false"><span class="fa fa-search"></span></a>
                <div class="dropdown-menu">
                  <form action="/find" target="_blank">
                    <input type="text" placeholder="Card Search" class="form-control" name="q">
                  </form>
              </div>
            </li>

            <!-- locale selection -->

                                                                        <li class="dropdown">
              <a class="dropdown-toggle" data-toggle="dropdown">
                <span class="lang-sm" lang="en"></span>
                <span class="caret">
              </span></a>
              <ul class="dropdown-menu">
                                  <li>
                    <a href="/decklist/view/58581">
                      <span lang="en" class="lang-sm lang-lbl lang-lbl-full"></span>
                    </a>
                  </li>
                                  <li>
                    <a href="https://es.marvelcdb.com/decklist/view/58581">
                      <span lang="es" class="lang-sm lang-lbl lang-lbl-full"></span>
                    </a>
                  </li>
                                  <li>
                    <a href="https://fr.marvelcdb.com/decklist/view/58581">
                      <span lang="fr" class="lang-sm lang-lbl lang-lbl-full"></span>
                    </a>
                  </li>
                                  <li>
                    <a href="https://de.marvelcdb.com/decklist/view/58581">
                      <span lang="de" class="lang-sm lang-lbl lang-lbl-full"></span>
                    </a>
                  </li>
                                  <li>
                    <a href="https://it.marvelcdb.com/decklist/view/58581">
                      <span lang="it" class="lang-sm lang-lbl lang-lbl-full"></span>
                    </a>
                  </li>
                                  <li>
                    <a href="https://ko.marvelcdb.com/decklist/view/58581">
                      <span lang="ko" class="lang-sm lang-lbl lang-lbl-full"></span>
                    </a>
                  </li>
                              </ul>
            </li>
                        
            <li id="login">
                <a href="#" class="dropdown-toggle" data-toggle="dropdown"><span class="fa fa-user"></span><span class="caret"></span></a><ul class="dropdown-menu"><li><a href="/login">Login or Register</a></li></ul>
            </li>


          </ul>
          <form class="navbar-form navbar-right visible-lg-block visible-xs-block external" action="/find" target="_blank">
            <div class="form-group">
              <input type="text" placeholder="Card Search" class="form-control" name="q">
            </div>
          </form>
        </div><!--/.navbar-collapse -->
              </div>
    </nav>

<div class="container">
	<div class="row">
		<div class="col-xs-12">
			<h1 class="decklist-header text-center">
				<span class="icon icon-"></span>
				House of Pain
			</h1>
		</div>
		<div class="col-xs-12">
			<div class="social">
				<div class="pull-right">
					<span class="hidden-xs">published: </span>
					<time datetime="2026-01-24T14:08:32+00:00" title="Saturday, January 24, 2026 6:08 AM">2 days ago</time>
					<span class="social-icons">
	<span class="social-icon-like">
		<span class="fa fa-heart"></span> <span class="num">18</span>
	</span>
	<span class="social-icon-favorite">
		<span class="fa fa-star"></span> <span class="num">13</span>
	</span>
	<span class="social-icon-comment">
		<span class="fa fa-comment"></span> <span class="num">14</span>
	</span>
	<span class="social-icon-version" data-toggle="tooltip" data-placement="bottom" title="" data-original-title="Version">
		<span class="fa fa-code-fork"></span> <span class="num">1.0</span>
	
</span>

				</span></div>

			</div>
		</div>
	</div>
</div>

<div class="main white container">
	<div class="row">
		<div class="col-md-6">
			<div id="deck-content" style="margin-bottom:10px"><div class="deck-block" style="background-image: linear-gradient(100deg, #b42328 49.5%, #8c979b 50%, #8c979b 51%, #221e25 51.5%, #221e25 100%);"><div class="deck-header"><div class="deck-meta"><h4 style="font-weight:bold"><a class="card card-tip" data-toggle="modal" data-remote="false" data-target="#cardModal" data-code="13001a">Wasp (Nadia Van Dyne)</a></h4><div><span class="fa fa-circle fg-aggression" title="aggression"></span> Aggression (18)</div><div>42 cards </div><div><span onclick="$('#packs_required').toggle()" style="border-bottom: 1px dashed #cfcfcf;" title="Core Set, Wasp, The Galaxy's Most Wanted, Gamora, Vision, Nova, Ironheart, NeXt Evolution, Magneto, Winter Soldier, Civil War">11 packs required </span> <div style="display:none;" id="packs_required">Core Set, Wasp, The Galaxy's Most Wanted, Gamora, Vision, Nova, Ironheart, NeXt Evolution, Magneto, Winter Soldier, Civil War</div> </div><div>Multiplayer, Theme</div></div><div class="deck-hero-image"><div class="card-thumbnail-wide card-thumbnail-hero" style="background-position: -38px -33px;background-image:url(/bundles/cards/13001a.jpg)"></div><div class="card-thumbnail-wide card-thumbnail-hero" style="background-image:url(/bundles/cards/13001b.jpg)"></div></div></div><div class="deck-content"><div><div><h5><span class="icon icon-Ally"></span> Ally (5)</h5><div>1x  <span class="fa fa-circle fg-aggression" title="aggression"></span> •<span class="icon icon-ally icon-aggression"></span> <a href="https://marvelcdb.com/card/18011" class="card card-tip " data-toggle="modal" data-remote="false" data-target="#cardModal" data-code="18011">Angela</a><span style="float: right"> <span class="icon-mental color-mental" title="mental"></span></span></div><div>1x <span class="fa fa-user" style="color:grey;" title="Hero specific cards. Cannot be removed"></span> •<span class="icon icon-ally icon-hero"></span> <a href="https://marvelcdb.com/card/13002" class="card card-tip " data-toggle="modal" data-remote="false" data-target="#cardModal" data-code="13002">Ant-Man</a><span style="float: right"> <span class="icon-wild color-wild" title="wild"></span></span></div><div>1x  <span class="fa fa-circle fg-aggression" title="aggression"></span> •<span class="icon icon-ally icon-aggression"></span> <a href="https://marvelcdb.com/card/01050" class="card card-tip " data-toggle="modal" data-remote="false" data-target="#cardModal" data-code="01050">Hulk</a><span style="float: right"> <span class="icon-energy color-energy" title="energy"></span></span></div><div>1x  <span class="fa fa-circle fg-basic" title="basic"></span> •<span class="icon icon-ally icon-basic"></span> <a href="https://marvelcdb.com/card/13018" class="card card-tip " data-toggle="modal" data-remote="false" data-target="#cardModal" data-code="13018">Ironheart</a><span style="float: right"> <span class="icon-mental color-mental" title="mental"></span></span></div><div>1x  <span class="fa fa-circle fg-basic" title="basic"></span> •<span class="icon icon-ally icon-basic"></span> <a href="https://marvelcdb.com/card/28018" class="card card-tip " data-toggle="modal" data-remote="false" data-target="#cardModal" data-code="28018">Moon Girl</a><span style="float: right"> <span class="icon-mental color-mental" title="mental"></span></span></div></div><div><h5><span class="icon icon-Event"></span> Event (19)</h5><div>1x  <span class="fa fa-circle fg-basic" title="basic"></span><span class="icon icon-event icon-basic"></span> <a href="https://marvelcdb.com/card/49022" class="card card-tip " data-toggle="modal" data-remote="false" data-target="#cardModal" data-code="49022">Face the Past</a><span style="float: right"> <span class="icon-physical color-physical" title="physical"></span></span></div><div>2x <span class="fa fa-user" style="color:grey;" title="Hero specific cards. Cannot be removed"></span><span class="icon icon-event icon-hero"></span> <a href="https://marvelcdb.com/card/13003" class="card card-tip " data-toggle="modal" data-remote="false" data-target="#cardModal" data-code="13003">Giant Help</a><span style="float: right"> <span class="icon-mental color-mental" title="mental"></span></span></div><div>3x <span class="fa fa-user" style="color:grey;" title="Hero specific cards. Cannot be removed"></span><span class="icon icon-event icon-hero"></span> <a href="https://marvelcdb.com/card/13004" class="card card-tip " data-toggle="modal" data-remote="false" data-target="#cardModal" data-code="13004">Pinpoint Strike</a><span style="float: right"> <span class="icon-mental color-mental" title="mental"></span></span></div><div>2x <span class="fa fa-user" style="color:grey;" title="Hero specific cards. Cannot be removed"></span><span class="icon icon-event icon-hero"></span> <a href="https://marvelcdb.com/card/13005" class="card card-tip " data-toggle="modal" data-remote="false" data-target="#cardModal" data-code="13005">Rapid Growth</a><span style="float: right"> <span class="icon-energy color-energy" title="energy"></span></span></div><div>3x  <span class="fa fa-circle fg-aggression" title="aggression"></span><span class="icon icon-event icon-aggression"></span> <a href="https://marvelcdb.com/card/56017" class="card card-tip " data-toggle="modal" data-remote="false" data-target="#cardModal" data-code="56017">Savage Strike</a><span style="float: right"> <span class="icon-physical color-physical" title="physical"></span></span></div><div>3x  <span class="fa fa-circle fg-aggression" title="aggression"></span><span class="icon icon-event icon-aggression"></span> <a href="https://marvelcdb.com/card/54016" class="card card-tip " data-toggle="modal" data-remote="false" data-target="#cardModal" data-code="54016">Spoiling for a Fight</a><span style="float: right"> <span class="icon-energy color-energy" title="energy"></span></span></div><div>3x  <span class="fa fa-circle fg-aggression" title="aggression"></span><span class="icon icon-event icon-aggression"></span> <a href="https://marvelcdb.com/card/13014" class="card card-tip " data-toggle="modal" data-remote="false" data-target="#cardModal" data-code="13014">Surprise Attack</a><span style="float: right"> <span class="icon-physical color-physical" title="physical"></span></span></div><div>2x <span class="fa fa-user" style="color:grey;" title="Hero specific cards. Cannot be removed"></span><span class="icon icon-event icon-hero"></span> <a href="https://marvelcdb.com/card/13006" class="card card-tip " data-toggle="modal" data-remote="false" data-target="#cardModal" data-code="13006">Wasp Sting</a><span style="float: right"> <span class="icon-mental color-mental" title="mental"></span></span></div></div><div><h5><span class="icon icon-Player Side Scheme"></span> Player Side Scheme (1)</h5><div>1x  <span class="fa fa-circle fg-aggression" title="aggression"></span> •<span class="icon icon-player_side_scheme icon-aggression"></span> <a href="https://marvelcdb.com/card/40019" class="card card-tip " data-toggle="modal" data-remote="false" data-target="#cardModal" data-code="40019">Lock and Load</a><span style="float: right"> <span class="icon-physical color-physical" title="physical"></span></span></div></div><div><h5><span class="icon icon-Resource"></span> Resource (5)</h5><div>1x  <span class="fa fa-circle fg-basic" title="basic"></span><span class="icon icon-resource icon-basic"></span> <a href="https://marvelcdb.com/card/01088" class="card card-tip " data-toggle="modal" data-remote="false" data-target="#cardModal" data-code="01088">Energy</a><span style="float: right"> <span class="icon-energy color-energy" title="energy"></span> <span class="icon-energy color-energy" title="energy"></span></span></div><div>1x  <span class="fa fa-circle fg-basic" title="basic"></span><span class="icon icon-resource icon-basic"></span> <a href="https://marvelcdb.com/card/01089" class="card card-tip " data-toggle="modal" data-remote="false" data-target="#cardModal" data-code="01089">Genius</a><span style="float: right"> <span class="icon-mental color-mental" title="mental"></span> <span class="icon-mental color-mental" title="mental"></span></span></div><div>2x <span class="fa fa-user" style="color:grey;" title="Hero specific cards. Cannot be removed"></span><span class="icon icon-resource icon-hero"></span> <a href="https://marvelcdb.com/card/13007" class="card card-tip " data-toggle="modal" data-remote="false" data-target="#cardModal" data-code="13007">Pym Particles</a><span style="float: right"> <span class="icon-wild color-wild" title="wild"></span></span></div><div>1x  <span class="fa fa-circle fg-basic" title="basic"></span><span class="icon icon-resource icon-basic"></span> <a href="https://marvelcdb.com/card/01090" class="card card-tip " data-toggle="modal" data-remote="false" data-target="#cardModal" data-code="01090">Strength</a><span style="float: right"> <span class="icon-physical color-physical" title="physical"></span> <span class="icon-physical color-physical" title="physical"></span></span></div></div></div><div><div><h5><span class="icon icon-Support"></span> Support (4)</h5><div>2x  <span class="fa fa-circle fg-aggression" title="aggression"></span><span class="icon icon-support icon-aggression"></span> <a href="https://marvelcdb.com/card/26033" class="card card-tip " data-toggle="modal" data-remote="false" data-target="#cardModal" data-code="26033">Assault Training</a><span style="float: right"> <span class="icon-mental color-mental" title="mental"></span></span></div><div>1x  <span class="fa fa-circle fg-basic" title="basic"></span><span class="icon icon-support icon-basic"></span> <a href="https://marvelcdb.com/card/01091" class="card card-tip " data-toggle="modal" data-remote="false" data-target="#cardModal" data-code="01091">Avengers Mansion</a><span style="float: right"> <span class="icon-mental color-mental" title="mental"></span></span></div><div>1x  <span class="fa fa-circle fg-basic" title="basic"></span> •<span class="icon icon-support icon-basic"></span> <a href="https://marvelcdb.com/card/08023" class="card card-tip " data-toggle="modal" data-remote="false" data-target="#cardModal" data-code="08023">Quincarrier</a><span style="float: right"> <span class="icon-mental color-mental" title="mental"></span></span></div></div><div><h5><span class="icon icon-Upgrade"></span> Upgrade (8)</h5><div>1x  <span class="fa fa-circle fg-aggression" title="aggression"></span><span class="icon icon-upgrade icon-aggression"></span> <a href="https://marvelcdb.com/card/56013" class="card card-tip " data-toggle="modal" data-remote="false" data-target="#cardModal" data-code="56013">Aggressive Conditioning</a><span style="float: right"> <span class="icon-physical color-physical" title="physical"></span></span></div><div>1x <span class="fa fa-user" style="color:grey;" title="Hero specific cards. Cannot be removed"></span> •<span class="icon icon-upgrade icon-hero"></span> <a href="https://marvelcdb.com/card/13009" class="card card-tip " data-toggle="modal" data-remote="false" data-target="#cardModal" data-code="13009">Bio-Synthetic Wings</a><span style="float: right"> <span class="icon-energy color-energy" title="energy"></span></span></div><div>1x  <span class="fa fa-circle fg-aggression" title="aggression"></span><span class="icon icon-upgrade icon-aggression"></span> <a href="https://marvelcdb.com/card/01057" class="card card-tip " data-toggle="modal" data-remote="false" data-target="#cardModal" data-code="01057">Combat Training</a><span style="float: right"> <span class="icon-physical color-physical" title="physical"></span></span></div><div>1x  <span class="fa fa-circle fg-aggression" title="aggression"></span> •<span class="icon icon-upgrade icon-aggression"></span> <a href="https://marvelcdb.com/card/18018" class="card card-tip " data-toggle="modal" data-remote="false" data-target="#cardModal" data-code="18018">Godslayer</a><span style="float: right"> <span class="icon-mental color-mental" title="mental"></span></span></div><div>1x  <span class="fa fa-circle fg-aggression" title="aggression"></span><span class="icon icon-upgrade icon-aggression"></span> <a href="https://marvelcdb.com/card/16046" class="card card-tip " data-toggle="modal" data-remote="false" data-target="#cardModal" data-code="16046">Hand Cannon</a><span style="float: right"> <span class="icon-physical color-physical" title="physical"></span></span></div><div>1x  <span class="fa fa-circle fg-basic" title="basic"></span><span class="icon icon-upgrade icon-basic"></span> <a href="https://marvelcdb.com/card/29027" class="card card-tip " data-toggle="modal" data-remote="false" data-target="#cardModal" data-code="29027">Ingenuity</a><span style="float: right"> <span class="icon-mental color-mental" title="mental"></span></span></div><div>1x <span class="fa fa-user" style="color:grey;" title="Hero specific cards. Cannot be removed"></span><span class="icon icon-upgrade icon-hero"></span> <a href="https://marvelcdb.com/card/13008" class="card card-tip " data-toggle="modal" data-remote="false" data-target="#cardModal" data-code="13008">Red Room Training</a><span style="float: right"> <span class="icon-physical color-physical" title="physical"></span></span></div><div>1x <span class="fa fa-user" style="color:grey;" title="Hero specific cards. Cannot be removed"></span> •<span class="icon icon-upgrade icon-hero"></span> <a href="https://marvelcdb.com/card/13010" class="card card-tip " data-toggle="modal" data-remote="false" data-target="#cardModal" data-code="13010">Wasp's Helmet</a><span style="float: right"> <span class="icon-physical color-physical" title="physical"></span></span></div></div> <div></div></div></div></div></div>
			<div class="row">
	<div class="col-sm-6">
		<div id="deck-chart-resource" style="width: 100%; height: 250px; overflow: hidden;" data-highcharts-chart="0"><div id="highcharts-z0ktr0a-0" dir="ltr" class="highcharts-container " style="position: relative; overflow: hidden; width: 262px; height: 250px; text-align: left; line-height: normal; z-index: 0; -webkit-tap-highlight-color: rgba(0, 0, 0, 0); user-select: none;"><svg version="1.1" class="highcharts-root" style="font-family:&quot;Lucida Grande&quot;, &quot;Lucida Sans Unicode&quot;, Arial, Helvetica, sans-serif;font-size:12px;" xmlns="http://www.w3.org/2000/svg" width="262" height="250" viewBox="0 0 262 250"><desc>Created with Highcharts 8.1.2</desc><defs><clipPath id="highcharts-z0ktr0a-1-"><rect x="0" y="0" width="213" height="142" fill="none"></rect></clipPath></defs><rect fill="#ffffff" class="highcharts-background" x="0" y="0" width="262" height="250" rx="0" ry="0"></rect><rect fill="none" class="highcharts-plot-background" x="39" y="53" width="213" height="142"></rect><g class="highcharts-grid highcharts-xaxis-grid" data-z-index="1"><path fill="none" data-z-index="1" class="highcharts-grid-line" d="M 91.5 53 L 91.5 195" opacity="1"></path><path fill="none" data-z-index="1" class="highcharts-grid-line" d="M 145.5 53 L 145.5 195" opacity="1"></path><path fill="none" data-z-index="1" class="highcharts-grid-line" d="M 198.5 53 L 198.5 195" opacity="1"></path><path fill="none" data-z-index="1" class="highcharts-grid-line" d="M 251.5 53 L 251.5 195" opacity="1"></path><path fill="none" data-z-index="1" class="highcharts-grid-line" d="M 38.5 53 L 38.5 195" opacity="1"></path></g><g class="highcharts-grid highcharts-xaxis-grid" data-z-index="1"></g><g class="highcharts-grid highcharts-yaxis-grid" data-z-index="1"><path fill="none" stroke="#e6e6e6" stroke-width="1" data-z-index="1" class="highcharts-grid-line" d="M 39 195.5 L 252 195.5" opacity="1"></path><path fill="none" stroke="#e6e6e6" stroke-width="1" data-z-index="1" class="highcharts-grid-line" d="M 39 175.5 L 252 175.5" opacity="1"></path><path fill="none" stroke="#e6e6e6" stroke-width="1" data-z-index="1" class="highcharts-grid-line" d="M 39 154.5 L 252 154.5" opacity="1"></path><path fill="none" stroke="#e6e6e6" stroke-width="1" data-z-index="1" class="highcharts-grid-line" d="M 39 134.5 L 252 134.5" opacity="1"></path><path fill="none" stroke="#e6e6e6" stroke-width="1" data-z-index="1" class="highcharts-grid-line" d="M 39 114.5 L 252 114.5" opacity="1"></path><path fill="none" stroke="#e6e6e6" stroke-width="1" data-z-index="1" class="highcharts-grid-line" d="M 39 94.5 L 252 94.5" opacity="1"></path><path fill="none" stroke="#e6e6e6" stroke-width="1" data-z-index="1" class="highcharts-grid-line" d="M 39 73.5 L 252 73.5" opacity="1"></path><path fill="none" stroke="#e6e6e6" stroke-width="1" data-z-index="1" class="highcharts-grid-line" d="M 39 52.5 L 252 52.5" opacity="1"></path></g><rect fill="none" class="highcharts-plot-border" data-z-index="1" x="39" y="53" width="213" height="142"></rect><g class="highcharts-axis highcharts-xaxis" data-z-index="2"><path fill="none" class="highcharts-axis-line" stroke="#ccd6eb" stroke-width="1" data-z-index="7" d="M 39 195.5 L 252 195.5"></path></g><g class="highcharts-axis highcharts-xaxis" data-z-index="2"><path fill="none" class="highcharts-axis-line" stroke="#ccd6eb" stroke-width="1" data-z-index="7" d="M 39 235.5 L 252 235.5"></path></g><g class="highcharts-axis highcharts-yaxis" data-z-index="2"><path fill="none" class="highcharts-axis-line" data-z-index="7" d="M 39 53 L 39 195"></path></g><g class="highcharts-series-group" data-z-index="3"><g class="highcharts-series highcharts-series-0 highcharts-column-series highcharts-color-0 highcharts-tracker" data-z-index="0.1" opacity="1" transform="translate(39,53) scale(1 1)" clip-path="url(#highcharts-z0ktr0a-1-)"><rect x="5" y="42" width="43" height="87" fill="#661e09" opacity="1" class="highcharts-point highcharts-color-0 highcharts-drilldown-point" style="cursor:pointer;"></rect><rect x="59" y="21" width="43" height="75" fill="#003961" opacity="1" class="highcharts-point highcharts-color-0 highcharts-drilldown-point" style="cursor:pointer;"></rect><rect x="112" y="82" width="43" height="41" fill="#ff8f3f" opacity="1" class="highcharts-point highcharts-color-0 highcharts-drilldown-point" style="cursor:pointer;"></rect><rect x="165" y="123" width="43" height="0" fill="#00543a" opacity="1" class="highcharts-point highcharts-color-0 highcharts-drilldown-point" style="cursor:pointer;"></rect></g><g class="highcharts-markers highcharts-series-0 highcharts-column-series highcharts-color-0" data-z-index="0.1" opacity="1" transform="translate(39,53) scale(1 1)" clip-path="none"></g><g class="highcharts-series highcharts-series-1 highcharts-column-series highcharts-color-1 highcharts-tracker" data-z-index="0.1" opacity="1" transform="translate(39,53) scale(1 1)" clip-path="url(#highcharts-z0ktr0a-1-)"><rect x="5" y="129" width="43" height="14" fill="#434348" opacity="1" class="highcharts-point highcharts-color-1"></rect><rect x="59" y="96" width="43" height="47" fill="#434348" opacity="1" class="highcharts-point highcharts-color-1"></rect><rect x="112" y="123" width="43" height="20" fill="#434348" opacity="1" class="highcharts-point highcharts-color-1"></rect><rect x="165" y="123" width="43" height="20" fill="#434348" opacity="1" class="highcharts-point highcharts-color-1"></rect></g><g class="highcharts-markers highcharts-series-1 highcharts-column-series highcharts-color-1" data-z-index="0.1" opacity="1" transform="translate(39,53) scale(1 1)" clip-path="none"></g></g><text x="131" text-anchor="middle" class="highcharts-title" data-z-index="4" style="color:#333333;font-size:18px;fill:#333333;" y="24"><tspan>Card Skill Icons</tspan></text><text x="131" text-anchor="middle" class="highcharts-subtitle" data-z-index="4" style="color:#666666;fill:#666666;" y="52"></text><text x="10" text-anchor="start" class="highcharts-caption" data-z-index="4" style="color:#666666;fill:#666666;" y="247"></text><g class="highcharts-legend" data-z-index="7"><rect fill="none" class="highcharts-legend-box" rx="0" ry="0" x="0" y="0" width="8" height="8" visibility="hidden"></rect><g data-z-index="1"><g></g></g></g><g class="highcharts-axis-labels highcharts-xaxis-labels" data-z-index="7"></g><g class="highcharts-axis-labels highcharts-xaxis-labels" data-z-index="7"></g><g class="highcharts-axis-labels highcharts-yaxis-labels" data-z-index="7"><text x="24" style="color:#666666;cursor:default;font-size:11px;fill:#666666;" text-anchor="end" transform="translate(0,0)" y="199" opacity="1">0</text><text x="24" style="color:#666666;cursor:default;font-size:11px;fill:#666666;" text-anchor="end" transform="translate(0,0)" y="179" opacity="1">3</text><text x="24" style="color:#666666;cursor:default;font-size:11px;fill:#666666;" text-anchor="end" transform="translate(0,0)" y="158" opacity="1">6</text><text x="24" style="color:#666666;cursor:default;font-size:11px;fill:#666666;" text-anchor="end" transform="translate(0,0)" y="138" opacity="1">9</text><text x="24" style="color:#666666;cursor:default;font-size:11px;fill:#666666;" text-anchor="end" transform="translate(0,0)" y="118" opacity="1">12</text><text x="24" style="color:#666666;cursor:default;font-size:11px;fill:#666666;" text-anchor="end" transform="translate(0,0)" y="98" opacity="1">15</text><text x="24" style="color:#666666;cursor:default;font-size:11px;fill:#666666;" text-anchor="end" transform="translate(0,0)" y="77" opacity="1">18</text><text x="24" style="color:#666666;cursor:default;font-size:11px;fill:#666666;" text-anchor="end" transform="translate(0,0)" y="57" opacity="1">21</text></g><text x="252" class="highcharts-credits" text-anchor="end" data-z-index="8" style="cursor:pointer;color:#999999;font-size:9px;fill:#999999;" y="245">Highcharts.com</text></svg><div class="highcharts-axis-labels highcharts-xaxis-labels" style="position: absolute; left: 0px; top: 0px; opacity: 1;"><span style="position: absolute; font-family: &quot;Lucida Grande&quot;, &quot;Lucida Sans Unicode&quot;, Arial, Helvetica, sans-serif; font-size: 11px; white-space: nowrap; margin-left: 0px; margin-top: 0px; left: 60.125px; top: 203px; color: rgb(0, 51, 153); cursor: pointer; transform: rotate(0deg); transform-origin: 50% 11px; opacity: 1; font-weight: bold; text-decoration: underline;" opacity="1" class="highcharts-drilldown-axis-label"><span class="icon icon-physical color-physical"></span></span><span style="position: absolute; font-family: &quot;Lucida Grande&quot;, &quot;Lucida Sans Unicode&quot;, Arial, Helvetica, sans-serif; font-size: 11px; white-space: nowrap; margin-left: 0px; margin-top: 0px; left: 113.375px; top: 203px; color: rgb(0, 51, 153); cursor: pointer; transform: rotate(0deg); transform-origin: 50% 11px; opacity: 1; font-weight: bold; text-decoration: underline;" opacity="1" class="highcharts-drilldown-axis-label"><span class="icon icon-mental color-mental"></span></span><span style="position: absolute; font-family: &quot;Lucida Grande&quot;, &quot;Lucida Sans Unicode&quot;, Arial, Helvetica, sans-serif; font-size: 11px; white-space: nowrap; margin-left: 0px; margin-top: 0px; left: 166.625px; top: 203px; color: rgb(0, 51, 153); cursor: pointer; transform: rotate(0deg); transform-origin: 50% 11px; opacity: 1; font-weight: bold; text-decoration: underline;" opacity="1" class="highcharts-drilldown-axis-label"><span class="icon icon-energy color-energy"></span></span><span style="position: absolute; font-family: &quot;Lucida Grande&quot;, &quot;Lucida Sans Unicode&quot;, Arial, Helvetica, sans-serif; font-size: 11px; white-space: nowrap; margin-left: 0px; margin-top: 0px; left: 219.875px; top: 203px; color: rgb(0, 51, 153); cursor: pointer; transform: rotate(0deg); transform-origin: 50% 11px; opacity: 1; font-weight: bold; text-decoration: underline;" opacity="1" class="highcharts-drilldown-axis-label"><span class="icon icon-wild color-wild"></span></span></div></div></div>
	</div>
	<div class="col-sm-6">
		<div id="deck-chart-cost" style="width: 100%; height: 250px; overflow: hidden;" data-highcharts-chart="1"><div id="highcharts-z0ktr0a-12" dir="ltr" class="highcharts-container " style="position: relative; overflow: hidden; width: 262px; height: 250px; text-align: left; line-height: normal; z-index: 0; -webkit-tap-highlight-color: rgba(0, 0, 0, 0); user-select: none;"><svg version="1.1" class="highcharts-root" style="font-family:&quot;Lucida Grande&quot;, &quot;Lucida Sans Unicode&quot;, Arial, Helvetica, sans-serif;font-size:12px;" xmlns="http://www.w3.org/2000/svg" width="262" height="250" viewBox="0 0 262 250"><desc>Created with Highcharts 8.1.2</desc><defs><clipPath id="highcharts-z0ktr0a-13-"><rect x="0" y="0" width="213" height="142" fill="none"></rect></clipPath></defs><rect fill="#ffffff" class="highcharts-background" x="0" y="0" width="262" height="250" rx="0" ry="0"></rect><rect fill="none" class="highcharts-plot-background" x="39" y="71" width="213" height="142"></rect><g class="highcharts-grid highcharts-xaxis-grid" data-z-index="1"><path fill="none" data-z-index="1" class="highcharts-grid-line" d="M 40.5 71 L 40.5 213" opacity="1"></path><path fill="none" data-z-index="1" class="highcharts-grid-line" d="M 92.5 71 L 92.5 213" opacity="1"></path><path fill="none" data-z-index="1" class="highcharts-grid-line" d="M 145.5 71 L 145.5 213" opacity="1"></path><path fill="none" data-z-index="1" class="highcharts-grid-line" d="M 197.5 71 L 197.5 213" opacity="1"></path><path fill="none" data-z-index="1" class="highcharts-grid-line" d="M 249.5 71 L 249.5 213" opacity="1"></path></g><g class="highcharts-grid highcharts-yaxis-grid" data-z-index="1"><path fill="none" stroke="#e6e6e6" stroke-width="1" data-z-index="1" class="highcharts-grid-line" d="M 39 213.5 L 252 213.5" opacity="1"></path><path fill="none" stroke="#e6e6e6" stroke-width="1" data-z-index="1" class="highcharts-grid-line" d="M 39 193.5 L 252 193.5" opacity="1"></path><path fill="none" stroke="#e6e6e6" stroke-width="1" data-z-index="1" class="highcharts-grid-line" d="M 39 172.5 L 252 172.5" opacity="1"></path><path fill="none" stroke="#e6e6e6" stroke-width="1" data-z-index="1" class="highcharts-grid-line" d="M 39 152.5 L 252 152.5" opacity="1"></path><path fill="none" stroke="#e6e6e6" stroke-width="1" data-z-index="1" class="highcharts-grid-line" d="M 39 132.5 L 252 132.5" opacity="1"></path><path fill="none" stroke="#e6e6e6" stroke-width="1" data-z-index="1" class="highcharts-grid-line" d="M 39 112.5 L 252 112.5" opacity="1"></path><path fill="none" stroke="#e6e6e6" stroke-width="1" data-z-index="1" class="highcharts-grid-line" d="M 39 91.5 L 252 91.5" opacity="1"></path><path fill="none" stroke="#e6e6e6" stroke-width="1" data-z-index="1" class="highcharts-grid-line" d="M 39 70.5 L 252 70.5" opacity="1"></path></g><rect fill="none" class="highcharts-plot-border" data-z-index="1" x="39" y="71" width="213" height="142"></rect><g class="highcharts-axis highcharts-xaxis" data-z-index="2"><path fill="none" class="highcharts-tick" stroke="#ccd6eb" stroke-width="1" d="M 40.5 213 L 40.5 223" opacity="1"></path><path fill="none" class="highcharts-tick" stroke="#ccd6eb" stroke-width="1" d="M 92.5 213 L 92.5 223" opacity="1"></path><path fill="none" class="highcharts-tick" stroke="#ccd6eb" stroke-width="1" d="M 145.5 213 L 145.5 223" opacity="1"></path><path fill="none" class="highcharts-tick" stroke="#ccd6eb" stroke-width="1" d="M 197.5 213 L 197.5 223" opacity="1"></path><path fill="none" class="highcharts-tick" stroke="#ccd6eb" stroke-width="1" d="M 249.5 213 L 249.5 223" opacity="1"></path><path fill="none" class="highcharts-axis-line" stroke="#ccd6eb" stroke-width="1" data-z-index="7" d="M 39 213.5 L 252 213.5"></path></g><g class="highcharts-axis highcharts-yaxis" data-z-index="2"><path fill="none" class="highcharts-axis-line" data-z-index="7" d="M 39 71 L 39 213"></path></g><g class="highcharts-series-group" data-z-index="3"><g class="highcharts-series highcharts-series-0 highcharts-line-series highcharts-color-0" data-z-index="0.1" opacity="1" transform="translate(39,71) scale(1 1)" clip-path="url(#highcharts-z0ktr0a-13-)"><path fill="none" d="M 2.0882352941176 91.28571428571429 L 54.294117647059 60.85714285714286 L 106.5 20.285714285714292 L 158.70588235294 40.571428571428584 L 210.91176470588 121.71428571428572" class="highcharts-graph" data-z-index="1" stroke="#7cb5ec" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"></path><path fill="none" d="M 2.0882352941176 91.28571428571429 L 54.294117647059 60.85714285714286 L 106.5 20.285714285714292 L 158.70588235294 40.571428571428584 L 210.91176470588 121.71428571428572" visibility="visible" data-z-index="2" class="highcharts-tracker-line" stroke-linecap="round" stroke-linejoin="round" stroke="rgba(192,192,192,0.0001)" stroke-width="22"></path></g><g class="highcharts-markers highcharts-series-0 highcharts-line-series highcharts-color-0 highcharts-tracker" data-z-index="0.1" opacity="1" transform="translate(39,71) scale(1 1)" clip-path="none"><path fill="#7cb5ec" d="M 2.0000000000000004 95 A 4 4 0 1 1 2.003999999333336 94.99999800000016 Z" opacity="1" class="highcharts-point highcharts-color-0"></path><path fill="#7cb5ec" d="M 54 65 A 4 4 0 1 1 54.00399999933334 64.99999800000016 Z" opacity="1" class="highcharts-point highcharts-color-0"></path><path fill="#7cb5ec" d="M 106 24 A 4 4 0 1 1 106.00399999933333 23.99999800000017 Z" opacity="1" class="highcharts-point highcharts-color-0"></path><path fill="#7cb5ec" d="M 158 45 A 4 4 0 1 1 158.00399999933333 44.99999800000017 Z" opacity="1" class="highcharts-point highcharts-color-0"></path><path fill="#7cb5ec" d="M 210 126 A 4 4 0 1 1 210.00399999933333 125.99999800000016 Z" opacity="1" class="highcharts-point highcharts-color-0"></path></g></g><text x="131" text-anchor="middle" class="highcharts-title" data-z-index="4" style="color:#333333;font-size:18px;fill:#333333;" y="24"><tspan>Card Cost</tspan></text><text x="131" text-anchor="middle" class="highcharts-subtitle" data-z-index="4" style="color:#666666;fill:#666666;" y="52"><tspan>Cost X ignored</tspan></text><text x="10" text-anchor="start" class="highcharts-caption" data-z-index="4" style="color:#666666;fill:#666666;" y="247"></text><g class="highcharts-legend" data-z-index="7"><rect fill="none" class="highcharts-legend-box" rx="0" ry="0" x="0" y="0" width="8" height="8" visibility="hidden"></rect><g data-z-index="1"><g></g></g></g><g class="highcharts-axis-labels highcharts-xaxis-labels" data-z-index="7"><text x="41.088235294118" style="color:#666666;cursor:default;font-size:11px;fill:#666666;" text-anchor="middle" transform="translate(0,0)" y="232" opacity="1">0</text><text x="93.294117647059" style="color:#666666;cursor:default;font-size:11px;fill:#666666;" text-anchor="middle" transform="translate(0,0)" y="232" opacity="1">1</text><text x="145.5" style="color:#666666;cursor:default;font-size:11px;fill:#666666;" text-anchor="middle" transform="translate(0,0)" y="232" opacity="1">2</text><text x="197.70588235294" style="color:#666666;cursor:default;font-size:11px;fill:#666666;" text-anchor="middle" transform="translate(0,0)" y="232" opacity="1">3</text><text x="248.5" style="color:#666666;cursor:default;font-size:11px;fill:#666666;" text-anchor="middle" transform="translate(0,0)" y="232" opacity="1">4</text></g><g class="highcharts-axis-labels highcharts-yaxis-labels" data-z-index="7"><text x="24" style="color:#666666;cursor:default;font-size:11px;fill:#666666;" text-anchor="end" transform="translate(0,0)" y="217" opacity="1">0</text><text x="24" style="color:#666666;cursor:default;font-size:11px;fill:#666666;" text-anchor="end" transform="translate(0,0)" y="197" opacity="1">2</text><text x="24" style="color:#666666;cursor:default;font-size:11px;fill:#666666;" text-anchor="end" transform="translate(0,0)" y="176" opacity="1">4</text><text x="24" style="color:#666666;cursor:default;font-size:11px;fill:#666666;" text-anchor="end" transform="translate(0,0)" y="156" opacity="1">6</text><text x="24" style="color:#666666;cursor:default;font-size:11px;fill:#666666;" text-anchor="end" transform="translate(0,0)" y="136" opacity="1">8</text><text x="24" style="color:#666666;cursor:default;font-size:11px;fill:#666666;" text-anchor="end" transform="translate(0,0)" y="116" opacity="1">10</text><text x="24" style="color:#666666;cursor:default;font-size:11px;fill:#666666;" text-anchor="end" transform="translate(0,0)" y="95" opacity="1">12</text><text x="24" style="color:#666666;cursor:default;font-size:11px;fill:#666666;" text-anchor="end" transform="translate(0,0)" y="75" opacity="1">14</text></g><text x="252" class="highcharts-credits" text-anchor="end" data-z-index="8" style="cursor:pointer;color:#999999;font-size:9px;fill:#999999;" y="245">Highcharts.com</text></svg></div></div>
	</div>
	<div class="col-sm-6">
		<div id="deck-chart-faction" style="width: 100%; height: 250px; overflow: hidden;" data-highcharts-chart="2"><div id="highcharts-z0ktr0a-20" dir="ltr" class="highcharts-container " style="position: relative; overflow: hidden; width: 262px; height: 250px; text-align: left; line-height: normal; z-index: 0; -webkit-tap-highlight-color: rgba(0, 0, 0, 0); user-select: none;"><svg version="1.1" class="highcharts-root" style="font-family:&quot;Lucida Grande&quot;, &quot;Lucida Sans Unicode&quot;, Arial, Helvetica, sans-serif;font-size:12px;" xmlns="http://www.w3.org/2000/svg" width="262" height="250" viewBox="0 0 262 250"><desc>Created with Highcharts 8.1.2</desc><defs><clipPath id="highcharts-z0ktr0a-21-"><rect x="0" y="0" width="213" height="164" fill="none"></rect></clipPath></defs><rect fill="#ffffff" class="highcharts-background" x="0" y="0" width="262" height="250" rx="0" ry="0"></rect><rect fill="none" class="highcharts-plot-background" x="39" y="71" width="213" height="164"></rect><g class="highcharts-grid highcharts-xaxis-grid" data-z-index="1"><path fill="none" data-z-index="1" class="highcharts-grid-line" d="M 109.5 71 L 109.5 235" opacity="1"></path><path fill="none" data-z-index="1" class="highcharts-grid-line" d="M 180.5 71 L 180.5 235" opacity="1"></path><path fill="none" data-z-index="1" class="highcharts-grid-line" d="M 251.5 71 L 251.5 235" opacity="1"></path><path fill="none" data-z-index="1" class="highcharts-grid-line" d="M 38.5 71 L 38.5 235" opacity="1"></path></g><g class="highcharts-grid highcharts-yaxis-grid" data-z-index="1"><path fill="none" stroke="#e6e6e6" stroke-width="1" data-z-index="1" class="highcharts-grid-line" d="M 39 235.5 L 252 235.5" opacity="1"></path><path fill="none" stroke="#e6e6e6" stroke-width="1" data-z-index="1" class="highcharts-grid-line" d="M 39 212.5 L 252 212.5" opacity="1"></path><path fill="none" stroke="#e6e6e6" stroke-width="1" data-z-index="1" class="highcharts-grid-line" d="M 39 188.5 L 252 188.5" opacity="1"></path><path fill="none" stroke="#e6e6e6" stroke-width="1" data-z-index="1" class="highcharts-grid-line" d="M 39 165.5 L 252 165.5" opacity="1"></path><path fill="none" stroke="#e6e6e6" stroke-width="1" data-z-index="1" class="highcharts-grid-line" d="M 39 141.5 L 252 141.5" opacity="1"></path><path fill="none" stroke="#e6e6e6" stroke-width="1" data-z-index="1" class="highcharts-grid-line" d="M 39 118.5 L 252 118.5" opacity="1"></path><path fill="none" stroke="#e6e6e6" stroke-width="1" data-z-index="1" class="highcharts-grid-line" d="M 39 94.5 L 252 94.5" opacity="1"></path><path fill="none" stroke="#e6e6e6" stroke-width="1" data-z-index="1" class="highcharts-grid-line" d="M 39 70.5 L 252 70.5" opacity="1"></path></g><rect fill="none" class="highcharts-plot-border" data-z-index="1" x="39" y="71" width="213" height="164"></rect><g class="highcharts-axis highcharts-xaxis" data-z-index="2"><path fill="none" class="highcharts-axis-line" stroke="#ccd6eb" stroke-width="1" data-z-index="7" d="M 39 235.5 L 252 235.5"></path></g><g class="highcharts-axis highcharts-yaxis" data-z-index="2"><path fill="none" class="highcharts-axis-line" data-z-index="7" d="M 39 71 L 39 235"></path></g><g class="highcharts-series-group" data-z-index="3"><g class="highcharts-series highcharts-series-0 highcharts-column-series highcharts-color-0 highcharts-tracker" data-z-index="0.1" opacity="1" transform="translate(39,71) scale(1 1)" clip-path="url(#highcharts-z0ktr0a-21-)"><rect x="7" y="24" width="57" height="141" fill="#cc3038" opacity="1" class="highcharts-point highcharts-color-0"></rect><rect x="78" y="95" width="57" height="70" fill="#808080" opacity="1" class="highcharts-point highcharts-color-0"></rect><rect x="149" y="48" width="57" height="117" fill="#AB006A" opacity="1" class="highcharts-point highcharts-color-0"></rect></g><g class="highcharts-markers highcharts-series-0 highcharts-column-series highcharts-color-0" data-z-index="0.1" opacity="1" transform="translate(39,71) scale(1 1)" clip-path="none"></g></g><text x="131" text-anchor="middle" class="highcharts-title" data-z-index="4" style="color:#333333;font-size:18px;fill:#333333;" y="24"><tspan>Card Factions</tspan></text><text x="131" text-anchor="middle" class="highcharts-subtitle" data-z-index="4" style="color:#666666;fill:#666666;" y="52"><tspan>Draw deck only</tspan></text><text x="10" text-anchor="start" class="highcharts-caption" data-z-index="4" style="color:#666666;fill:#666666;" y="247"></text><g class="highcharts-legend" data-z-index="7"><rect fill="none" class="highcharts-legend-box" rx="0" ry="0" x="0" y="0" width="8" height="8" visibility="hidden"></rect><g data-z-index="1"><g></g></g></g><g class="highcharts-axis-labels highcharts-xaxis-labels" data-z-index="7"></g><g class="highcharts-axis-labels highcharts-yaxis-labels" data-z-index="7"><text x="24" style="color:#666666;cursor:default;font-size:11px;fill:#666666;" text-anchor="end" transform="translate(0,0)" y="239" opacity="1">0</text><text x="24" style="color:#666666;cursor:default;font-size:11px;fill:#666666;" text-anchor="end" transform="translate(0,0)" y="216" opacity="1">3</text><text x="24" style="color:#666666;cursor:default;font-size:11px;fill:#666666;" text-anchor="end" transform="translate(0,0)" y="192" opacity="1">6</text><text x="24" style="color:#666666;cursor:default;font-size:11px;fill:#666666;" text-anchor="end" transform="translate(0,0)" y="169" opacity="1">9</text><text x="24" style="color:#666666;cursor:default;font-size:11px;fill:#666666;" text-anchor="end" transform="translate(0,0)" y="145" opacity="1">12</text><text x="24" style="color:#666666;cursor:default;font-size:11px;fill:#666666;" text-anchor="end" transform="translate(0,0)" y="122" opacity="1">15</text><text x="24" style="color:#666666;cursor:default;font-size:11px;fill:#666666;" text-anchor="end" transform="translate(0,0)" y="98" opacity="1">18</text><text x="24" style="color:#666666;cursor:default;font-size:11px;fill:#666666;" text-anchor="end" transform="translate(0,0)" y="75" opacity="1">21</text></g><text x="252" class="highcharts-credits" text-anchor="end" data-z-index="8" style="cursor:pointer;color:#999999;font-size:9px;fill:#999999;" y="245">Highcharts.com</text></svg><div class="highcharts-axis-labels highcharts-xaxis-labels" style="position: absolute; left: 0px; top: 0px; opacity: 1;"><span style="position: absolute; font-family: &quot;Lucida Grande&quot;, &quot;Lucida Sans Unicode&quot;, Arial, Helvetica, sans-serif; font-size: 11px; white-space: nowrap; margin-left: 0px; margin-top: 0px; left: 74.5px; top: 243px; color: rgb(102, 102, 102); cursor: default; transform: rotate(0deg); transform-origin: 50% 11px; text-overflow: clip; opacity: 1;" opacity="1"><span class="icon icon-aggression"></span></span><span style="position: absolute; font-family: &quot;Lucida Grande&quot;, &quot;Lucida Sans Unicode&quot;, Arial, Helvetica, sans-serif; font-size: 11px; white-space: nowrap; margin-left: 0px; margin-top: 0px; left: 145.5px; top: 243px; color: rgb(102, 102, 102); cursor: default; transform: rotate(0deg); transform-origin: 50% 11px; text-overflow: clip; opacity: 1;" opacity="1"><span class="icon icon-basic"></span></span><span style="position: absolute; font-family: &quot;Lucida Grande&quot;, &quot;Lucida Sans Unicode&quot;, Arial, Helvetica, sans-serif; font-size: 11px; white-space: nowrap; margin-left: 0px; margin-top: 0px; left: 216.5px; top: 243px; color: rgb(102, 102, 102); cursor: default; transform: rotate(0deg); transform-origin: 50% 11px; text-overflow: clip; opacity: 1;" opacity="1"><span class="icon icon-hero"></span></span></div></div></div>
	</div>
	<div class="col-sm-6">
		<div id="deck-chart-types" style="width: 100%; height: 250px; overflow: hidden;" data-highcharts-chart="3"><div id="highcharts-z0ktr0a-26" dir="ltr" class="highcharts-container " style="position: relative; overflow: hidden; width: 262px; height: 250px; text-align: left; line-height: normal; z-index: 0; -webkit-tap-highlight-color: rgba(0, 0, 0, 0); user-select: none;"><svg version="1.1" class="highcharts-root" style="font-family:&quot;Lucida Grande&quot;, &quot;Lucida Sans Unicode&quot;, Arial, Helvetica, sans-serif;font-size:12px;" xmlns="http://www.w3.org/2000/svg" width="262" height="250" viewBox="0 0 262 250"><desc>Created with Highcharts 8.1.2</desc><defs><clipPath id="highcharts-z0ktr0a-33-"><rect x="0" y="0" width="242" height="164" fill="none"></rect></clipPath></defs><rect fill="#ffffff" class="highcharts-background" x="0" y="0" width="262" height="250" rx="0" ry="0"></rect><rect fill="none" class="highcharts-plot-background" x="10" y="71" width="242" height="164"></rect><rect fill="none" class="highcharts-plot-border" data-z-index="1" x="10" y="71" width="242" height="164"></rect><g class="highcharts-series-group" data-z-index="3"><g class="highcharts-series highcharts-series-0 highcharts-pie-series highcharts-tracker" data-z-index="0.1" opacity="1" transform="translate(10,71) scale(1 1)"><path fill="#1a7095" d="M 114.49185307185219 46.500000829655484 A 40 40 0 0 1 141.6716469602083 57.14524567519252 L 114.5 86.5 A 0 0 0 0 0 114.5 86.5 Z" transform="translate(0,0)" stroke="#ffffff" stroke-width="1" opacity="1" stroke-linejoin="round" class="highcharts-point highcharts-color-0"></path><path fill="#004106" d="M 141.7009881238183 57.17243199500006 A 40 40 0 0 1 151.74953221869998 101.07643130152343 L 114.5 86.5 A 0 0 0 0 0 114.5 86.5 Z" transform="translate(0,0)" stroke="#ffffff" stroke-width="1" opacity="1" stroke-linejoin="round" class="highcharts-point highcharts-color-1"></path><path fill="#a07000" d="M 151.73493716506331 101.11367353931882 A 40 40 0 0 1 131.89128512573387 122.52142697999938 L 114.5 86.5 A 0 0 0 0 0 114.5 86.5 Z" transform="translate(0,0)" stroke="#ffffff" stroke-width="1" opacity="1" stroke-linejoin="round" class="highcharts-point highcharts-color-2"></path><path fill="#f7a35c" d="M 131.85525500911564 122.53880025151457 A 40 40 0 0 1 108.5935305462068 126.06151688941424 L 114.5 86.5 A 0 0 0 0 0 114.5 86.5 Z" transform="translate(0,0)" stroke="#ffffff" stroke-width="1" opacity="1" stroke-linejoin="round" class="highcharts-point highcharts-color-3"></path><path fill="#ac1018" d="M 108.55397198914545 126.05559064018806 A 40 40 0 0 1 108.50709065149027 46.9514850147247 L 114.5 86.5 A 0 0 0 0 0 114.5 86.5 Z" transform="translate(0,0)" stroke="#ffffff" stroke-width="1" opacity="1" stroke-linejoin="round" class="highcharts-point highcharts-color-4"></path><path fill="#606060" d="M 108.54664215633856 46.94551188063085 A 40 40 0 0 1 114.44444080247713 46.50003858532398 L 114.5 86.5 A 0 0 0 0 0 114.5 86.5 Z" transform="translate(0,0)" stroke="#ffffff" stroke-width="1" opacity="1" stroke-linejoin="round" class="highcharts-point highcharts-color-5"></path></g><g class="highcharts-markers highcharts-series-0 highcharts-pie-series" data-z-index="0.1" opacity="1" transform="translate(10,71) scale(1 1)"></g></g><text x="131" text-anchor="middle" class="highcharts-title" data-z-index="4" style="color:#333333;font-size:18px;fill:#333333;" y="24"><tspan>Card Types</tspan></text><text x="131" text-anchor="middle" class="highcharts-subtitle" data-z-index="4" style="color:#666666;fill:#666666;" y="52"><tspan>Draw deck only</tspan></text><text x="10" text-anchor="start" class="highcharts-caption" data-z-index="4" style="color:#666666;fill:#666666;" y="247"></text><g class="highcharts-data-labels highcharts-series-0 highcharts-pie-series highcharts-tracker" data-z-index="6" opacity="1" transform="translate(10,71) scale(1 1)"><path fill="none" class="highcharts-data-label-connector highcharts-color-0" stroke="#1a7095" stroke-width="1" d="M 145.07387170564763 21.3388375949057 C 140.07387170564763 21.3388375949057 133.49773326705255 38.09456507050138 131.30568712085417 43.679807562366605 L 129.1136409746558 49.26505005423183"></path><path fill="none" class="highcharts-data-label-connector highcharts-color-1" stroke="#004106" stroke-width="1" d="M 187.74495385272763 70.92353462305798 C 182.74495385272763 70.92353462305798 165.1962514334548 74.92891143427163 159.34668396036386 76.26403703800952 L 153.49711648727293 77.59916264174741"></path><path fill="none" class="highcharts-data-label-connector highcharts-color-2" stroke="#a07000" stroke-width="1" d="M 172.26362383309169 132.5 C 167.26362383309169 132.5 152.61869733515096 121.8689823640878 148.220386104172 117.78794593746228 L 143.82207487319306 113.70690951083677"></path><path fill="none" class="highcharts-data-label-connector highcharts-color-3" stroke="#f7a35c" stroke-width="1" d="M 129.93295863233215 156.5 C 124.93295863233215 156.5 122.2501978411611 137.9192029637067 121.35594424410405 131.98621800635593 L 120.461690647047 126.05323304900514"></path><path fill="none" class="highcharts-data-label-connector highcharts-color-4" stroke="#ac1018" stroke-width="1" d="M 39.5 86.50000000000007 C 44.5 86.50000000000007 62.5 86.50000000000004 68.5 86.50000000000004 L 74.5 86.50000000000004"></path><path fill="none" class="highcharts-data-label-connector highcharts-color-5" stroke="#606060" stroke-width="1" d="M 104.26889344895028 16.695734197317396 C 109.26889344895028 16.695734197317396 110.61403513350588 34.64540254657864 111.06241569502443 40.62862532966572 L 111.51079625654297 46.611848112752796"></path><g class="highcharts-label highcharts-data-label highcharts-data-label-color-0" data-z-index="1" transform="translate(150,11)"><text x="5" data-z-index="1" y="16" style="color:#000000;font-size:11px;font-weight:bold;fill:#000000;"><tspan x="5" y="16" class="highcharts-text-outline" fill="#FFFFFF" stroke="#FFFFFF" stroke-width="2px" stroke-linejoin="round" style="">Ally</tspan><tspan x="5" y="16">Ally</tspan></text></g><g class="highcharts-label highcharts-data-label highcharts-data-label-color-1" data-z-index="1" transform="translate(193,61)"><text x="5" data-z-index="1" y="16" style="color:#000000;font-size:11px;font-weight:bold;fill:#000000;"><tspan x="5" y="16" class="highcharts-text-outline" fill="#FFFFFF" stroke="#FFFFFF" stroke-width="2px" stroke-linejoin="round" style="">Upgra…</tspan><tspan x="5" y="16">Upgra…</tspan><title>Upgrade</title></text></g><g class="highcharts-label highcharts-data-label highcharts-data-label-color-2" data-z-index="1" transform="translate(177,123)"><text x="5" data-z-index="1" y="16" style="color:#000000;font-size:11px;font-weight:bold;fill:#000000;"><tspan x="5" y="16" class="highcharts-text-outline" fill="#FFFFFF" stroke="#FFFFFF" stroke-width="2px" stroke-linejoin="round" style="">Resource</tspan><tspan x="5" y="16">Resource</tspan></text></g><g class="highcharts-label highcharts-data-label highcharts-data-label-color-3" data-z-index="1" transform="translate(135,147)"><text x="5" data-z-index="1" y="16" style="color:#000000;font-size:11px;font-weight:bold;fill:#000000;"><tspan x="5" y="16" class="highcharts-text-outline" fill="#FFFFFF" stroke="#FFFFFF" stroke-width="2px" stroke-linejoin="round" style="">Support</tspan><tspan x="5" y="16">Support</tspan></text></g><g class="highcharts-label highcharts-data-label highcharts-data-label-color-4" data-z-index="1" transform="translate(-10,77)"><text x="5" data-z-index="1" y="16" style="color:#000000;font-size:11px;font-weight:bold;fill:#000000;"><tspan x="5" y="16" class="highcharts-text-outline" fill="#FFFFFF" stroke="#FFFFFF" stroke-width="2px" stroke-linejoin="round" style="">Eve…</tspan><tspan x="5" y="16">Eve…</tspan><title>Event</title></text></g><g class="highcharts-label highcharts-data-label highcharts-data-label-color-5" data-z-index="1" transform="translate(30,7)"><text x="5" data-z-index="1" y="16" style="color:#000000;font-size:11px;font-weight:bold;fill:#000000;"><tspan x="5" y="16" class="highcharts-text-outline" fill="#FFFFFF" stroke="#FFFFFF" stroke-width="2px" stroke-linejoin="round" style="">Player Side</tspan><tspan dy="14" x="5" class="highcharts-text-outline" fill="#FFFFFF" stroke="#FFFFFF" stroke-width="2px" stroke-linejoin="round" style="">Scheme</tspan><tspan x="5" y="16">Player Side</tspan><tspan dy="14" x="5">Scheme</tspan></text></g></g><g class="highcharts-legend" data-z-index="7"><rect fill="none" class="highcharts-legend-box" rx="0" ry="0" x="0" y="0" width="8" height="8" visibility="hidden"></rect><g data-z-index="1"><g></g></g></g><text x="252" class="highcharts-credits" text-anchor="end" data-z-index="8" style="cursor:pointer;color:#999999;font-size:9px;fill:#999999;" y="245">Highcharts.com</text></svg></div></div>
	</div>
</div>
			<!-- Draw Simulator -->
<div id="table-draw-simulator">
	<h3><span class="fa fa-repeat"></span> Card draw simulator</h3>
	<div class="text-center" title="Click to draw; Shift-click to reset and draw">
		<div class="btn-group">
			<button class="btn btn-default btn-sm" disabled="disabled">Draw:</button>
			<button class="btn btn-default btn-sm" data-command="1">1</button>
			<button class="btn btn-default btn-sm" data-command="2">2</button>
			<button class="btn btn-default btn-sm" data-command="6">6</button>
			<button class="btn btn-default btn-sm" data-command="hero_hand">hero hand</button>
			<button class="btn btn-default btn-sm" data-command="alterego_hand">alterego hand</button>
			<button class="btn btn-default btn-sm" data-command="all">all</button>
		</div>
		<div class="btn-group">
			<button class="btn btn-default btn-sm" data-command="redraw" disabled="disabled">Redraw Selected</button>
			<button class="btn btn-default btn-sm" data-command="reshuffle" disabled="disabled">Reshuffle Selected</button>
			<button class="btn btn-default btn-sm" data-command="clear" disabled="disabled">Reset</button>
		</div>
		<div title="Odds to have at least 1 copy of a desired card, after having drawn that many cards from the deck, depending of the number of copies in the deck (1 - 2 - 3)">
			<span class="small">Odds: 
				<span id="draw-simulator-odds-1">0</span>% – 
				<span id="draw-simulator-odds-2">0</span>% – 
				<span id="draw-simulator-odds-3">0</span>% 
				<a href="#oddsModal" id="draw-simulator-more" data-toggle="modal" style="margin:0 10px">more</a>
			</span>
		</div>
	</div>
	<div id="table-draw-simulator-content"></div>
</div>			<table class="table table-condensed" id="table-predecessor">
<thead>
<tr><th colspan="1"><span class="fa fa-backward"></span> Derived from</th></tr>
</thead>
<tbody>
<tr><td>None. Self-made deck here.</td></tr>
</tbody>
</table>
			<table class="table table-condensed" id="table-successor">
<thead>
<tr><th colspan="1"><span class="fa fa-forward"></span> Inspiration for</th></tr>
</thead>
<tbody>
<tr><td>None yet</td></tr>
</tbody>
</table>
		</div>
		<div class="col-md-6">
			<div class="row">
				<div class="col-md-12">
					<div class="pull-right btn-group" role="group"><a href="/decklist/edit/58581" title="Edit decklist name / description" id="decklist-edit" class="btn btn-sm btn-default" style="display:none">
	<span class="fa fa-pencil text-primary"></span> Edit
</a>
<a href="#" title="Delete decklist" id="decklist-delete" class="btn btn-sm btn-default" style="display:none">
	<span class="fa fa-trash-o text-danger"></span> Delete
</a>
<a href="/deck/copy/58581" class="btn btn-sm btn-default">
	<span class="fa fa-save"></span> <span class="hidden-xs">Copy</span>
</a>
<div class="btn-group">
	<button type="button" class="btn btn-sm btn-default dropdown-toggle " data-toggle="dropdown">
		<span class="fa fa-download"></span> <span class="hidden-xs">Download</span> <span class="caret"></span>
	</button>
	<ul class="dropdown-menu" role="menu">
		<li><a href="#" id="btn-download-text">Text file</a></li>
		<li><a href="#" id="btn-download-octgn">Octgn file</a></li>
	</ul>
</div>
<div class="btn-group">
	<button type="button" class="btn btn-sm btn-default dropdown-toggle " data-toggle="dropdown">
		<span class="fa fa-sort"></span> <span class="hidden-xs">Sort</span> <span class="caret"></span>
	</button>
	<ul class="dropdown-menu" role="menu" id="menu-sort">
		<li><a href="#" onclick="app.deck.change_sort('default')" id="btn-sort-default">by Type</a></li>
		<li><a href="#" onclick="app.deck.change_sort('name')" id="btn-sort-name">by Name</a></li>
		<li><a href="#" onclick="app.deck.change_sort('number')" id="btn-sort-faction">by Card Number</a></li>
		<li><a href="#" onclick="app.deck.change_sort('cost')" id="btn-sort-faction">by Cost</a></li>
		<li><a href="#" onclick="app.deck.change_sort('set')" id="btn-sort-position">by Set, then Name</a></li>
		<li><a href="#" onclick="app.deck.change_sort('settype')" id="btn-sort-position">by Set, then Type</a></li>
		<li><a href="#" onclick="app.deck.change_sort('setnumber')" id="btn-sort-position">by Set, then Card Number</a></li>
		<li><a href="#" onclick="app.deck.change_sort('faction')" id="btn-sort-faction">by Aspect, then Name</a></li>
		<li><a href="#" onclick="app.deck.change_sort('factiontype')" id="btn-sort-faction">by Aspect, then Type</a></li>
		<li><a href="#" onclick="app.deck.change_sort('factioncost')" id="btn-sort-faction">by Aspect, then Cost</a></li>
		<li><a href="#" onclick="app.deck.change_sort('factionnumber')" id="btn-sort-faction">by Aspect, then Card Number</a></li>
	</ul>
</div>
</div>
				</div>
				<div class="col-md-12">
					<h3 class="username">
	<span class="fa fa-user"></span>
    <a href="/user/profile/6643/boomguy" class="username fg-pool">boomguy</a>
 · <small title="User Reputation">11771</small>

</h3>
<div id="deck-description"><p><strong></strong></p><center><strong>   <span style="font-size:x-large;"> <img class="img-responsive" src="https://lh5.googleusercontent.com/proxy/pVZbak5efd9InQtwZUOten7Gz7HH-J7akC27c6gW5FGYCiYRCxID0VUpvSdngZxkkfhqZmhcoBagYrv7k0VdWYu7dBOKppgUIwdT38SraOM8fxI0xCFTbUZMC00bg3d65H00q5Nxv0NXkUJIgizdXJA7RptN" alt=""> </span></strong></center><strong></strong>
<hr>
<blockquote>
<h3><em>Pack it up, pack it in, let me begin</em></h3>
<h3><em>I came to win, battle me, that's a sin</em></h3>
</blockquote>
<hr>
<p><strong></strong></p><center><strong>   <span style="color:#B22222;font-size:x-large;"> Deck Overview </span></strong></center><strong></strong>
<p><strong>This is a low to medium complexity, multiplayer deck focusing on boosting damage for Wasp so that she can lean into splitting that damage in Giant form. It uses several cards that are not very common (or popular) in the community, including <a href="/card/56017">Savage Strike</a> and <a href="/card/18018">Godslayer</a>.</strong></p>
<p><strong>At the time of publishing, no decks using Wasp and Savage Strike exist! It's time to invite your enemies to the House of Pain. Jumping around is not optional.</strong></p>
<table>
<thead>
<tr>
<th>&nbsp;</th>
</tr>
</thead>
<tbody>
<tr>
<td>Player Type:</td>
<td>Johnny</td>
</tr>
<tr>
<td>Player Count:</td>
<td>2 - 4p</td>
</tr>
<tr>
<td>Key Cards:</td>
<td>Savage Strike, Godslayer</td>
</tr>
<tr>
<td>Complexity:</td>
<td>★★☆☆☆</td>
</tr>
<tr>
<td>Damage:</td>
<td>★★★★★</td>
</tr>
<tr>
<td>Threat Control:</td>
<td>★★☆☆☆</td>
</tr>
<tr>
<td>Survivability:</td>
<td>★★☆☆☆</td>
</tr>
<tr>
<td>Economy:</td>
<td>★★★☆☆</td>
</tr>
<tr>
<td>Card Drawing:</td>
<td>★★☆☆☆</td>
</tr>
</tbody>
</table>
<hr>
<p><strong></strong></p><center><strong>   <span style="color:#B22222;font-size:x-large;"> Deck Description </span></strong></center><strong></strong>
<p>Everyone always says, "Wasp loves <span class="icon-mental"></span> so she can shuffle cards in with her Alter-Ego ability."</p>
<p>*F*<em> that.</em></p>
<p>Let's forget about that for this deck, and talk about the <strong>real</strong> standout ability Wasp has: </p>
<p><em>"Damage you deal using your basic attack power (ATK) can be divided among enemies as you choose."</em></p>
<p><em>Now</em> we are getting somewhere. </p>
<p>Wasp has a basic ATK of 1 (tiny) and 2 (GIANT). We can get Wasp's basic attack pretty high using:</p>
<ul>
<li><a href="/card/01057">Combat Training</a> +1</li>
<li><a href="/card/56013">Aggressive Conditioning</a> +1</li>
<li><a href="/card/18018">Godslayer</a> +2 (when attacking a unique enemy)</li>
</ul>
<p>When combined with <a href="/card/13010">Wasp's Helmet</a>, which gives you +1ATK in tiny form, you will have a base attack of 6 in both forms once your upgrades are in play. (<a href="/card/13005">Rapid Growth</a> can also give us a temporary +2ATK boost in Giant form).</p>
<p>Now, the fun part. Using Wasp's ability on her Giant form, we can spread damage as needed. We will always choose to attack the villain whenever possible, and using <a href="/card/56017">Savage Strike</a> (which also negates tough cards; all instances of damage that you spread around now have piercing) as often as we can. You'll attack the villain and <em>accidentally</em> kill minions by spreading damage where you need it. </p>
<hr>
<blockquote>
<h3><em>Word to your moms, I came to drop bombs</em></h3>
<h3><em>I got more rhymes than the Bible's got Psalms</em></h3>
</blockquote>
<hr>
<p><strong></strong></p><center><strong>   <span style="font-size:x-large;"> <img class="img-responsive" src="https://i.imgflip.com/1nen7l.jpg" alt=""></span></strong></center><strong></strong>
<hr>
<blockquote>
<h3><em>And just like the Prodigal Son, I've returned</em></h3>
<h3><em>Anyone steppin' to me, you'll get burned</em></h3>
</blockquote>
<hr>
<p><strong>Other tidbits:</strong></p>
<ul>
<li><a href="/card/16046">Hand Cannon</a> is here to deal with Guard minions, since that would waste your spread damage (damage is applied simultaneously, so even if you deal some damage to kill the Guard minion, you can't then put any on the villain)</li>
<li><a href="/card/54016">Spoiling for a Fight</a> is great, since you get to ready and attack again, and the spread damage means you're happy to kill it using only what it needs to be defeated and then trigger <a href="/card/06018">Battle Fury</a> and <a href="/card/45043">Blood Rage</a></li>
<li><a href="/card/40019">Lock and Load</a> can grab a weapon, since <a href="/card/18018">Godslayer</a> is expensive, but can also grab <a href="/card/16046">Hand Cannon</a> if Godslayer is already in play</li>
<li><a href="/card/26033">Assault Training</a> is here to shuffle <a href="/card/56017">Savage Strike</a> back into the deck--and can itself be shuffled in using Wasp's Alter-Ego ability</li>
<li>Allies are here primarily to help keep you alive, and are just good value; you could swap them for others if you prefer</li>
<li>Since you're swapping forms anyway, <a href="/card/13014">Surprise Attack</a> is a solid inclusion to get some more damage onto the table</li>
</ul>
<hr>
<p><strong></strong></p><center><strong>   <span style="font-size:x-large;"> <img class="img-responsive" src="https://i.imgflip.com/7w8zue.jpg" alt=""> </span></strong></center><strong></strong>
<hr>
<blockquote>
<h1><em>So get out your seat and jump around</em></h1>
</blockquote>
<hr></div>
				</div>
				<div class="col-md-12">
					<table class="table">
<thead>
<tr><th><span class="fa fa-comment"></span> 14 comments</th></tr>
</thead>
<tbody>
<tr><td id="comment-24727">
    <div class="small comment-toggler" style="display:none">
        <a href="#div-comment-24727" data-toggle="collapse" class="text-muted pull-right" style="margin-left:.5em"><span class="fa fa-eye"></span></a>
    </div>
    <div class="collapse in" id="div-comment-24727">
    	<h4 class="comment-header">
    		<span class="comment-date pull-right" title="Sat, 24 Jan 2026 14:22:00 +0000">Jan 24, 2026</span>
        	<span class="comment-author"><a href="/user/profile/37471/DanTheCrow" class="username fg-encounter">DanTheCrow</a>
 · <small title="User Reputation">62</small>
</span>
    	</h4>
        <div class="comment-text"><p>Haha - that write up is amazing…. Another 42 card masterpiece</p></div>
    </div>
</td></tr>
<tr><td id="comment-24728">
    <div class="small comment-toggler" style="display:none">
        <a href="#div-comment-24728" data-toggle="collapse" class="text-muted pull-right" style="margin-left:.5em"><span class="fa fa-eye"></span></a>
    </div>
    <div class="collapse in" id="div-comment-24728">
    	<h4 class="comment-header">
    		<span class="comment-date pull-right" title="Sat, 24 Jan 2026 14:24:55 +0000">Jan 24, 2026</span>
        	<span class="comment-author"><a href="/user/profile/6643/boomguy" class="username fg-pool">boomguy</a>
 · <small title="User Reputation">11771</small>
</span>
    	</h4>
        <div class="comment-text"><p><code>@DanTheCrow</code> Much obliged, good sir! I hope you try out this deck with my favorite triple-form hero.</p></div>
    </div>
</td></tr>
<tr><td id="comment-24730">
    <div class="small comment-toggler" style="display:none">
        <a href="#div-comment-24730" data-toggle="collapse" class="text-muted pull-right" style="margin-left:.5em"><span class="fa fa-eye"></span></a>
    </div>
    <div class="collapse in" id="div-comment-24730">
    	<h4 class="comment-header">
    		<span class="comment-date pull-right" title="Sat, 24 Jan 2026 15:13:46 +0000">Jan 24, 2026</span>
        	<span class="comment-author"><a href="/user/profile/20057/MAXFightMan" class="username fg-">MAXFightMan</a>
 · <small title="User Reputation">128</small>
</span>
    	</h4>
        <div class="comment-text"><p>The sum is greater than the parts. The mark of a true decksman. I love to see Wasp coming out of the binder and I love to see more of these unique aggression decks. Thanks for sharing!</p></div>
    </div>
</td></tr>
<tr><td id="comment-24731">
    <div class="small comment-toggler" style="display:none">
        <a href="#div-comment-24731" data-toggle="collapse" class="text-muted pull-right" style="margin-left:.5em"><span class="fa fa-eye"></span></a>
    </div>
    <div class="collapse in" id="div-comment-24731">
    	<h4 class="comment-header">
    		<span class="comment-date pull-right" title="Sat, 24 Jan 2026 15:39:40 +0000">Jan 24, 2026</span>
        	<span class="comment-author"><a href="/user/profile/41089/JacenSketch" class="username fg-aggression">JacenSketch</a>
 · <small title="User Reputation">602</small>
</span>
    	</h4>
        <div class="comment-text"><p>This looks great! Wasp is a ton of fun! The thought of her carrying a giant Sword around in tiny form cracks me up. </p>
<p>Great use of a very fun form change hero!</p></div>
    </div>
</td></tr>
<tr><td id="comment-24732">
    <div class="small comment-toggler" style="display:none">
        <a href="#div-comment-24732" data-toggle="collapse" class="text-muted pull-right" style="margin-left:.5em"><span class="fa fa-eye"></span></a>
    </div>
    <div class="collapse in" id="div-comment-24732">
    	<h4 class="comment-header">
    		<span class="comment-date pull-right" title="Sat, 24 Jan 2026 15:42:14 +0000">Jan 24, 2026</span>
        	<span class="comment-author"><a href="/user/profile/6643/boomguy" class="username fg-pool">boomguy</a>
 · <small title="User Reputation">11771</small>
</span>
    	</h4>
        <div class="comment-text"><p><code>@MAXFightMan</code> Thank you for the kind words! Wasp is so much fun. I hope you give this one a try. </p>
<p><code>@JacenSketch</code> The only that we need to know: Does the sword shrink/grow when she does?</p></div>
    </div>
</td></tr>
<tr><td id="comment-24733">
    <div class="small comment-toggler" style="display:none">
        <a href="#div-comment-24733" data-toggle="collapse" class="text-muted pull-right" style="margin-left:.5em"><span class="fa fa-eye"></span></a>
    </div>
    <div class="collapse in" id="div-comment-24733">
    	<h4 class="comment-header">
    		<span class="comment-date pull-right" title="Sat, 24 Jan 2026 15:46:35 +0000">Jan 24, 2026</span>
        	<span class="comment-author"><a href="/user/profile/7073/D.M.Tip" class="username fg-protection">D.M.Tip</a>
 · <small title="User Reputation">3172</small>
</span>
    	</h4>
        <div class="comment-text"><p>Love it! Great use for Savage Strike. Props for the song being stuck in my brain again, haha.</p></div>
    </div>
</td></tr>
<tr><td id="comment-24734">
    <div class="small comment-toggler" style="display:none">
        <a href="#div-comment-24734" data-toggle="collapse" class="text-muted pull-right" style="margin-left:.5em"><span class="fa fa-eye"></span></a>
    </div>
    <div class="collapse in" id="div-comment-24734">
    	<h4 class="comment-header">
    		<span class="comment-date pull-right" title="Sat, 24 Jan 2026 16:38:48 +0000">Jan 24, 2026</span>
        	<span class="comment-author"><a href="/user/profile/41089/JacenSketch" class="username fg-aggression">JacenSketch</a>
 · <small title="User Reputation">602</small>
</span>
    	</h4>
        <div class="comment-text"><p><code>@boomguy</code> the world may never know.</p></div>
    </div>
</td></tr>
<tr><td id="comment-24737">
    <div class="small comment-toggler" style="display:none">
        <a href="#div-comment-24737" data-toggle="collapse" class="text-muted pull-right" style="margin-left:.5em"><span class="fa fa-eye"></span></a>
    </div>
    <div class="collapse in" id="div-comment-24737">
    	<h4 class="comment-header">
    		<span class="comment-date pull-right" title="Sat, 24 Jan 2026 19:21:46 +0000">Jan 24, 2026</span>
        	<span class="comment-author"><a href="/user/profile/37935/Swarles90" class="username fg-justice">Swarles90</a>
 · <small title="User Reputation">123</small>
</span>
    	</h4>
        <div class="comment-text"><p>I'll have to give this one a go - I've always wanted to build into her ability to spread damage around but never thought about using Savage Strike!</p></div>
    </div>
</td></tr>
<tr><td id="comment-24738">
    <div class="small comment-toggler" style="display:none">
        <a href="#div-comment-24738" data-toggle="collapse" class="text-muted pull-right" style="margin-left:.5em"><span class="fa fa-eye"></span></a>
    </div>
    <div class="collapse in" id="div-comment-24738">
    	<h4 class="comment-header">
    		<span class="comment-date pull-right" title="Sat, 24 Jan 2026 19:38:14 +0000">Jan 24, 2026</span>
        	<span class="comment-author"><a href="/user/profile/6643/boomguy" class="username fg-pool">boomguy</a>
 · <small title="User Reputation">11771</small>
</span>
    	</h4>
        <div class="comment-text"><p><code>@Swarles90</code> I didn’t find any other decks using her with <a href="/card/56017">Savage Strike</a>, at the time of posting this. It’s such fun combo and makes her ability to spread damage a lot more fun.</p></div>
    </div>
</td></tr>
<tr><td id="comment-24748">
    <div class="small comment-toggler" style="display:none">
        <a href="#div-comment-24748" data-toggle="collapse" class="text-muted pull-right" style="margin-left:.5em"><span class="fa fa-eye"></span></a>
    </div>
    <div class="collapse in" id="div-comment-24748">
    	<h4 class="comment-header">
    		<span class="comment-date pull-right" title="Sun, 25 Jan 2026 04:26:36 +0000">Jan 25, 2026</span>
        	<span class="comment-author"><a href="/user/profile/19660/BlueRiver" class="username fg-aggression">BlueRiver</a>
 · <small title="User Reputation">84</small>
</span>
    	</h4>
        <div class="comment-text"><p>The description is just... <img class="img-responsive" src="%5Bmedia0.giphy.com%5D(https%3A//media0.giphy.com/media/v1.Y2lkPTc5MGI3NjExYTI1ZXA2eTZhMjI4dzR0ZWRsYjUzajhtYmdpdW83Zmdjd3A3Yzd0YyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/2QSvHa1pqlcmBOeI77/giphy.gif)" height="150" alt="giphy.gif)"></p>
<p>Wasp is quite fun in Aggression. I love the <a href="/card/16046">Hand Cannon</a>s to get her ATK up to then spread it around as needed.</p></div>
    </div>
</td></tr>
<tr><td id="comment-24751">
    <div class="small comment-toggler" style="display:none">
        <a href="#div-comment-24751" data-toggle="collapse" class="text-muted pull-right" style="margin-left:.5em"><span class="fa fa-eye"></span></a>
    </div>
    <div class="collapse in" id="div-comment-24751">
    	<h4 class="comment-header">
    		<span class="comment-date pull-right" title="Sun, 25 Jan 2026 09:37:06 +0000">Jan 25, 2026</span>
        	<span class="comment-author"><a href="/user/profile/69548/R8C2" class="username fg-">R8C2</a>
 · <small title="User Reputation">125</small>
</span>
    	</h4>
        <div class="comment-text"><p>Nice deck! Wasp has had a big resurgence for me recently. Love her in aggression. And is there a hero better suited to using Savage Strike? It’s a really fun card for her.</p></div>
    </div>
</td></tr>
<tr><td id="comment-24752">
    <div class="small comment-toggler" style="display:none">
        <a href="#div-comment-24752" data-toggle="collapse" class="text-muted pull-right" style="margin-left:.5em"><span class="fa fa-eye"></span></a>
    </div>
    <div class="collapse in" id="div-comment-24752">
    	<h4 class="comment-header">
    		<span class="comment-date pull-right" title="Sun, 25 Jan 2026 10:54:13 +0000">Jan 25, 2026</span>
        	<span class="comment-author"><a href="/user/profile/6643/boomguy" class="username fg-pool">boomguy</a>
 · <small title="User Reputation">11771</small>
</span>
    	</h4>
        <div class="comment-text"><p><code>@BlueRiver</code> Thanks! Spreading her damage around has never been better! </p>
<p><code>@R8C2</code> Wasp is my favorite triple form hero, and it’s not close. I’ve been trying to figure out Savage Strike since it was released, and this might be the best place for it!</p></div>
    </div>
</td></tr>
<tr><td id="comment-24754">
    <div class="small comment-toggler" style="display:none">
        <a href="#div-comment-24754" data-toggle="collapse" class="text-muted pull-right" style="margin-left:.5em"><span class="fa fa-eye"></span></a>
    </div>
    <div class="collapse in" id="div-comment-24754">
    	<h4 class="comment-header">
    		<span class="comment-date pull-right" title="Sun, 25 Jan 2026 12:30:39 +0000">Jan 25, 2026</span>
        	<span class="comment-author"><a href="/user/profile/30132/UrinalSharts" class="username fg-campaign">UrinalSharts</a>
 · <small title="User Reputation">424</small>
</span>
    	</h4>
        <div class="comment-text"><p>I'm absolutely in love with Savage Strike. Looking forward to pulling Wasp out of hiding and sleecing this up.</p></div>
    </div>
</td></tr>
<tr><td id="comment-24755">
    <div class="small comment-toggler" style="display:none">
        <a href="#div-comment-24755" data-toggle="collapse" class="text-muted pull-right" style="margin-left:.5em"><span class="fa fa-eye"></span></a>
    </div>
    <div class="collapse in" id="div-comment-24755">
    	<h4 class="comment-header">
    		<span class="comment-date pull-right" title="Sun, 25 Jan 2026 13:23:11 +0000">Jan 25, 2026</span>
        	<span class="comment-author"><a href="/user/profile/6643/boomguy" class="username fg-pool">boomguy</a>
 · <small title="User Reputation">11771</small>
</span>
    	</h4>
        <div class="comment-text"><p><code>@UrinalSharts</code> Sleece it up, bro! Let me know how it goes for you!</p></div>
    </div>
</td></tr>
</tbody>
</table>
<a id="comment-form"></a><p>You must be logged in to post comments.</p>
				</div>
			</div>
		</div>
	</div>
</div>
<!-- Modal -->
<div class="modal fade" id="exportModal" tabindex="-1" role="dialog" aria-labelledby="exportModalLabel" aria-hidden="true">
	<div class="modal-dialog">
		<div class="modal-content">
			<div class="modal-header">
				<button type="button" class="close" data-dismiss="modal" aria-hidden="true">×</button>
				<h3 class="modal-title" id="exportModalLabel">Export decklist</h3>
			</div>
		    <div class="modal-body">
				<div class="row">
					<div class="col-md-12">
						<div class="form-group">
							<textarea class="form-control" id="export-deck" rows="20"></textarea>
						</div>
					</div><!-- /#modal-info -->
				</div><!-- /.row -->
			</div><!-- /.modal-body -->
		</div><!-- /.modal-content -->
	</div><!-- /.modal-dialog -->
</div><!-- /.modal -->
<!-- Modal -->
<!-- DeleteModal -->
<div class="modal fade" id="deleteModal" tabindex="-1" role="dialog" aria-labelledby="deleteModalLabel" aria-hidden="true">
	<div class="modal-dialog">
		<div class="modal-content">
			<div class="modal-header">
				<button type="button" class="close" data-dismiss="modal" aria-hidden="true">×</button>
				<h3 class="modal-title" id="deleteModalLabel">Delete decklist</h3>
			</div>
			<div class="modal-body">
				<div class="row">
					<div class="col-md-12">
						<form action="/decklist/delete/58581" method="POST" enctype="application/x-www-form-urlencoded" id="delete-decklistform">
							<input type="hidden" name="decklist_id" id="delete-decklist-id" value="58581">
							<p>Are you sure you want to delete this decklist?</p>
							<div class="pull-right">
								<button type="submit" id="btn-delete-submit" class="btn btn-danger">Yes, delete</button>
								<button type="button" class="btn btn-default" onclick="$('#deleteModal').modal('hide')">Cancel</button>
							</div>
						</form>
					</div><!-- /#modal-info -->
				</div><!-- /.row -->
			</div><!-- /.modal-body -->
		</div><!-- /.modal-content -->
	</div><!-- /.modal-dialog -->
</div><!-- /.modal -->
<!-- Modal -->
<!-- Modal -->
<div class="modal" id="oddsModal" tabindex="-1" role="dialog" aria-labelledby="oddsModalLabel" aria-hidden="true">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <button type="button" class="close" data-dismiss="modal" aria-hidden="true">×</button>
                <h3 class="modal-title" id="oddsModalLabel">Odds Calculator</h3>
            </div>
            <div class="modal-body">
                <div class="row">
                    <div class="col-sm-12">
						<form class="form-horizontal" role="form">
						    <div class="form-group">
						        <label for="odds-calculator-N" class="col-xs-7 control-label">Number of cards in deck</label>
						        <div class="col-xs-2">
						            <input type="number" class="form-control" id="odds-calculator-N" value="0">
								</div>
							</div>
							<div class="form-group">
								<label for="odds-calculator-K" class="col-xs-7 control-label">Number of <em>desired</em> cards in deck</label>
								<div class="col-xs-2">
									<input type="number" class="form-control" id="odds-calculator-K" value="0">
								</div>
							</div>
							<div class="form-group">
								<label for="odds-calculator-n" class="col-xs-7 control-label">Number of cards drawn</label>
								<div class="col-xs-2">
									<input type="number" class="form-control" id="odds-calculator-n" value="0">
								</div>
							</div>
							<div class="form-group">
								<label for="odds-calculator-k" class="col-xs-7 control-label">Number of <em>desired</em> cards in draw (at least)</label>
								<div class="col-xs-2">
									<input type="number" class="form-control" id="odds-calculator-k" value="0">
								</div>
							</div>
							<div class="form-group">
								<label class="col-xs-7 control-label">Probability of such an outcome</label>
								<div class="col-xs-2">
									 <p class="form-control-static"><span id="odds-calculator-p"></span>%</p>
								</div>
							</div>
						</form>
					</div>
				</div>
			</div>
		</div>
	</div>
</div>
<!-- Modal -->
<!-- Modal -->
<div class="modal fade" id="compareModal" tabindex="-1" role="dialog" aria-labelledby="compareModalLabel" aria-hidden="true">
	<div class="modal-dialog">
		<div class="modal-content">
			<div class="modal-header">
				<button type="button" class="close" data-dismiss="modal" aria-hidden="true">×</button>
				<h3 class="modal-title" id="compareModalLabel">Compare with another decklist</h3>
			</div>
			<div class="modal-body">
				<div class="row">
					<div class="col-md-12">
						<input type="hidden" name="decklist1_id" id="compare-decklist-id" value="58581">
						<div class="form-group">
							<label for="decklist2_url">Link or ID of the other decklist</label>
							<input type="text" class="form-control" name="decklist2_url" id="decklist2_url" maxlength="250" placeholder="Copy the URL link of a decklist">
						</div>
						<div class="pull-right">
							<button type="submit" id="btn-compare-submit" class="btn btn-success">Go</button>
							<button type="button" class="btn btn-default" onclick="$('#compareModal').modal('hide')">Cancel</button>
						</div>
					</div><!-- /#modal-info -->
				</div><!-- /.row -->
			</div><!-- /.modal-body -->
		</div><!-- /.modal-content -->
	</div><!-- /.modal-dialog -->
</div><!-- /.modal -->
<!-- Modal -->
    <div id="push"></div>
  </div>
  <footer class="hidden-print">
    <div class="container">

<div class="row">
    <div class="col-xs-12">

    <ul class="list-inline">
    <li><a href="/about">About</a></li>
    <li><a href="/api/">API</a></li>
    </ul>

    <p>
    Based on ThronesDB by Alsciende. Modified by Zzorba and Kam.
    Contact:
    <a href="https://reddit.com/user/kamalisk/" title="Reddit"><span class="fa fa-reddit"></span></a>
    </p>
    <p>
    Please post bug reports and feature requests on <a href="https://github.com/zzorba/marvelsdb">GitHub</a>
    </p>
    <p>
    I set up a <a href="https://www.patreon.com/kamalisk">Patreon</a> for those who want to help support the site.
    </p>
    <p>
    The information presented on this site about Marvel Champions: The Card Game, both literal and graphical, is copyrighted by Fantasy Flight Games.
    This website is not produced, endorsed, supported, or affiliated with Fantasy Flight Games.
    </p>

    </div>
</div>

    </div>
    </footer>
    <!--  card modal -->
<div class="modal" id="cardModal" tabindex="-1" role="dialog" aria-labelledby="cardModalLabel" aria-hidden="true">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <button type="button" class="close" data-dismiss="modal" aria-hidden="true">×</button>
                <h3 class="modal-title card-name">Modal title</h3>
                <div class="row modal-deck-options">
                    <div class="col-sm-7 text-center modal-deck-qty">
                        Deck Quantity: <div class="btn-group modal-qty" data-toggle="buttons"></div>
                    </div>
                    <div class="col-sm-5 text-center modal-deck-ignore">
                        Ignore Limit: <div class="btn-group modal-ignore" data-toggle="buttons"></div>
                    </div>
                </div>
            </div>
            <div class="modal-body">
                <div class="row">
                    <div class="col-sm-6 modal-image hidden-xs"></div>
                    <div class="col-sm-6 modal-info card-content"></div>
                </div>
            </div>
            <div class="modal-footer">
                <a role="button" href="#" class="btn btn-default card-modal-link">Go to card page</a>
                <button type="button" class="btn btn-primary" data-dismiss="modal">Close</button>
            </div>
        </div>
    </div>
</div>
<!--  /cardModal -->

    <script type="text/javascript" async="" src="https://www.googletagmanager.com/gtag/js?id=G-ED9N9069NF&amp;cx=c&amp;_slc=1"></script><script async="" src="//www.google-analytics.com/analytics.js"></script><script src="/bundles/fosjsrouting/js/router.js"></script>
    <script src="/js/routing?callback=fos.Router.setData"></script>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/2.1.4/jquery.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/underscore.js/1.8.3/underscore-min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/qtip2/2.1.1/jquery.qtip.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/typeahead.js/0.10.4/typeahead.jquery.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/marked/0.3.5/marked.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jquery.textcomplete/0.2.2/jquery.textcomplete.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/moment.js/2.10.6/moment.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highcharts/8.1.2/highcharts.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highcharts/8.1.2/modules/drilldown.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/bootstrap-markdown/2.9.0/js/bootstrap-markdown.min.js"></script>
    <script type="text/javascript">
    var app = {};
    moment.locale('en');
    $(function() {
            	});
    </script>

			<script async="" src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js"></script>
		<script>
(function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
(i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
})(window,document,'script','//www.google-analytics.com/analytics.js','ga');

ga('create', 'UA-83182253-2', 'auto');
ga('send', 'pageview');
</script>
	
		<script src="/js/app.js"></script>
	
			<script src="/js/b0ee8f9.js"></script>
		<script type="text/javascript">
	var Commenters = ["DanTheCrow","boomguy","MAXFightMan","JacenSketch","boomguy","D.M.Tip","JacenSketch","Swarles90","boomguy","BlueRiver","R8C2","boomguy","UrinalSharts","boomguy"];
	app.deck.init({"id":58581,"name":"House of Pain","date_creation":"2026-01-24T14:08:32+00:00","date_update":"2026-01-26T05:30:36+00:00","description_md":"**<center>   <span style=\"Verdana, Arial, Tahoma, Serif;; color:COLOUR; font-size:x-large;\"> ![](https:\/\/lh5.googleusercontent.com\/proxy\/pVZbak5efd9InQtwZUOten7Gz7HH-J7akC27c6gW5FGYCiYRCxID0VUpvSdngZxkkfhqZmhcoBagYrv7k0VdWYu7dBOKppgUIwdT38SraOM8fxI0xCFTbUZMC00bg3d65H00q5Nxv0NXkUJIgizdXJA7RptN) <\/center>**\r\n\r\n___\r\n\r\n> ### *Pack it up, pack it in, let me begin*\r\n\r\n> ### *I came to win, battle me, that's a sin*\r\n\r\n___\r\n\r\n**<center>   <span style=\"Verdana, Arial, Tahoma, Serif;; color:firebrick; font-size:x-large;\"> Deck Overview <\/center>**\r\n\r\n**This is a low to medium complexity, multiplayer deck focusing on boosting damage for Wasp so that she can lean into splitting that damage in Giant form. It uses several cards that are not very common (or popular) in the community, including [Savage Strike](\/card\/56017) and [Godslayer](\/card\/18018).**\r\n\r\n**At the time of publishing, no decks using Wasp and Savage Strike exist! It's time to invite your enemies to the House of Pain. Jumping around is not optional.**\r\n\r\n||&nbsp;|\r\n|-|-|\r\n| Player Type: || Johnny\r\n| Player Count: || 2 - 4p\r\n| Key Cards: || Savage Strike, Godslayer\r\n| Complexity:||\u2605\u2605\u2606\u2606\u2606 \r\n| Damage:||\u2605\u2605\u2605\u2605\u2605 \r\n| Threat Control:||\u2605\u2605\u2606\u2606\u2606 \r\n| Survivability:||\u2605\u2605\u2606\u2606\u2606\r\n| Economy:||\u2605\u2605\u2605\u2606\u2606\r\n| Card Drawing:||\u2605\u2605\u2606\u2606\u2606\r\n\r\n___\r\n\r\n**<center>   <span style=\"Verdana, Arial, Tahoma, Serif;; color:firebrick; font-size:x-large;\"> Deck Description <\/center>**\r\n\r\n\r\nEveryone always says, \"Wasp loves <span class=\"icon-mental\"><\/span> so she can shuffle cards in with her Alter-Ego ability.\"\r\n\r\n*F** that.*\r\n\r\nLet's forget about that for this deck, and talk about the **real** standout ability Wasp has: \r\n\r\n*\"Damage you deal using your basic attack power (ATK) can be divided among enemies as you choose.\"*\r\n\r\n*Now* we are getting somewhere. \r\n\r\nWasp has a basic ATK of 1 (tiny) and 2 (GIANT). We can get Wasp's basic attack pretty high using:\r\n\r\n - [Combat Training](\/card\/01057) +1\r\n - [Aggressive Conditioning](\/card\/56013) +1\r\n - [Godslayer](\/card\/18018) +2 (when attacking a unique enemy)\r\n\r\nWhen combined with [Wasp's Helmet](\/card\/13010), which gives you +1ATK in tiny form, you will have a base attack of 6 in both forms once your upgrades are in play. ([Rapid Growth](\/card\/13005) can also give us a temporary +2ATK boost in Giant form).\r\n\r\nNow, the fun part. Using Wasp's ability on her Giant form, we can spread damage as needed. We will always choose to attack the villain whenever possible, and using [Savage Strike](\/card\/56017) (which also negates tough cards; all instances of damage that you spread around now have piercing) as often as we can. You'll attack the villain and *accidentally* kill minions by spreading damage where you need it. \r\n___\r\n\r\n> ### *Word to your moms, I came to drop bombs*\r\n\r\n> ### *I got more rhymes than the Bible's got Psalms*\r\n\r\n___\r\n\r\n**<center>   <span style=\"Verdana, Arial, Tahoma, Serif;; color:COLOUR; font-size:x-large;\"> ![](https:\/\/i.imgflip.com\/1nen7l.jpg)<\/center>**\r\n___\r\n\r\n\r\n> ### *And just like the Prodigal Son, I've returned*\r\n\r\n> ### *Anyone steppin' to me, you'll get burned*\r\n\r\n___\r\n**Other tidbits:**\r\n - [Hand Cannon](\/card\/16046) is here to deal with Guard minions, since that would waste your spread damage (damage is applied simultaneously, so even if you deal some damage to kill the Guard minion, you can't then put any on the villain)\r\n - [Spoiling for a Fight](\/card\/54016) is great, since you get to ready and attack again, and the spread damage means you're happy to kill it using only what it needs to be defeated and then trigger [Battle Fury](\/card\/06018) and [Blood Rage](\/card\/45043)\r\n - [Lock and Load](\/card\/40019) can grab a weapon, since [Godslayer](\/card\/18018) is expensive, but can also grab [Hand Cannon](\/card\/16046) if Godslayer is already in play\r\n - [Assault Training](\/card\/26033) is here to shuffle [Savage Strike](\/card\/56017) back into the deck--and can itself be shuffled in using Wasp's Alter-Ego ability\r\n - Allies are here primarily to help keep you alive, and are just good value; you could swap them for others if you prefer\r\n - Since you're swapping forms anyway, [Surprise Attack](\/card\/13014) is a solid inclusion to get some more damage onto the table\r\n\r\n___\r\n\r\n**<center>   <span style=\"Verdana, Arial, Tahoma, Serif;; color:COLOUR; font-size:x-large;\"> ![](https:\/\/i.imgflip.com\/7w8zue.jpg) <\/center>**\r\n___\r\n\r\n> # *So get out your seat and jump around*\r\n\r\n___","user_id":6643,"hero_code":"13001a","hero_name":"Wasp","slots":{"01050":1,"01057":1,"01088":1,"01089":1,"01090":1,"01091":1,"08023":1,"13002":1,"13003":2,"13004":3,"13005":2,"13006":2,"13007":2,"13008":1,"13009":1,"13010":1,"13014":3,"13018":1,"16046":1,"18011":1,"18018":1,"26033":2,"28018":1,"29027":1,"40019":1,"49022":1,"54016":3,"56013":1,"56017":3},"ignoreDeckLimitSlots":null,"version":"1.0","meta":"{\"aspect\":\"aggression\"}","tags":"multiplayer, theme"});
	app.user.params.decklist_id = 58581;
	app.deck_upgrades && app.deck_upgrades.init([]);
	</script>
    

</body></html>
        '''
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = html.encode()
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        result = client.get_deck('58581')
        
        assert result.card_count() == 42
        assert result.id == '58581'
        assert result.name == 'House of Pain'
    
    def test_extract_deck_id_from_url(self, client):
        """Test extracting deck ID from URL"""
        url1 = '/decklist/view/12345'
        assert client._extract_deck_id_from_url(url1) == '12345'
        
        url2 = 'https://marvelcdb.com/decklist/view/67890'
        assert client._extract_deck_id_from_url(url2) == '67890'
        
        url3 = ''
        assert client._extract_deck_id_from_url(url3) is None
