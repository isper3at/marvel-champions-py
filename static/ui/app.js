(function(){
const e = React.createElement;
const { useState, useEffect, useRef } = React;

// Utility: simple fetch wrapper
async function fetchJson(path, opts){
  const res = await fetch(path, opts);
  if(!res.ok) throw new Error(await res.text());
  return res.json();
}

function App(){
  const [view, setView] = useState('lobby');
  const [room, setRoom] = useState(null);
  const [me, setMe] = useState(null);
  const [lobby, setLobby] = useState(null);
  const [moduleCards, setModuleCards] = useState(null);
  const [decksCache, setDecksCache] = useState(() => {
    try{ return JSON.parse(localStorage.getItem('decks')||'{}'); }catch(e){return{}}
  });
  const [socket, setSocket] = useState(null);

  useEffect(()=>{ localStorage.setItem('decks', JSON.stringify(decksCache)); }, [decksCache]);

  useEffect(()=>{
    // initialize socket once
    if(!socket){
      try{
        const s = io();
        setSocket(s);
        s.on('connect', ()=>console.log('socket connected', s.id));
        s.on('lobby_update', data => { if(data) setLobby(data); });
      }catch(e){ console.warn('socket init failed', e); }
    }

    if(socket && room){
      socket.emit('join_lobby', { room });
      // fetch initial snapshot
      (async ()=>{ try{ const j = await fetchJson(`/api/lobby/${room}`); setLobby(j); }catch(e){} })();
    }

    return ()=>{ if(socket && room) socket.emit('leave_lobby', { room }); };
  }, [room, socket]);

  if(view==='lobby') return e(LobbyView, { onCreate: async (host)=>{
    const j = await fetchJson('/api/lobby/create', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({host}) });
    setRoom(j.room); setMe({name:host}); setView('room');
  }, onJoin: async (roomId, name)=>{
    // join via API
    const p = await fetchJson(`/api/lobby/${roomId}/join`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({name}) });
    setRoom(roomId); setMe(p); setView('room');
  }});

  if(view==='room') return e(RoomView, { room, me, lobby, moduleCards, setModuleCards, decksCache, setDecksCache, onStart: ()=>setView('game') });

  if(view==='game') return e(GameView, { lobby, me, decksCache });

  return e('div', null, '...');
}

function LobbyView({ onCreate, onJoin }){
  const [host, setHost] = useState('Host');
  const [joinRoom, setJoinRoom] = useState('');
  const [joinName, setJoinName] = useState('Player');
  return e('div', {className:'card'},
    e('div', {className:'header'}, e('h2', null, 'Marvel Champions - Lobby')),
    e('div', {className:'flex'},
      e('div', {className:'card column'},
        e('h3', null, 'Create a room'),
        e('label', null, 'Host name'), e('input',{value:host,onChange:e=>setHost(e.target.value)}),
        e('div',{className:'controls'}, e('button',{onClick:()=>onCreate(host)}, 'Create'))
      ),
      e('div', {className:'card column'},
        e('h3', null, 'Join a room'),
        e('label', null, 'Room ID'), e('input',{value:joinRoom,onChange:e=>setJoinRoom(e.target.value)}),
        e('label', null, 'Your name'), e('input',{value:joinName,onChange:e=>setJoinName(e.target.value)}),
        e('div',{className:'controls'}, e('button',{onClick:()=>onJoin(joinRoom, joinName)}, 'Join'))
      )
    )
  );
}

function RoomView({ room, me, lobby, moduleCards, setModuleCards, decksCache, setDecksCache, onStart }){
  const [moduleName, setModuleName] = useState('');
  const [deckId, setDeckId] = useState('');
  const [myDeck, setMyDeck] = useState(null);
  const isHost = !lobby || (lobby.host === (me && me.name));

  async function fetchModule(name){
    if(!name) return;
    // check localStorage cache
    const cached = JSON.parse(localStorage.getItem('modules')||'{}')[name];
    if(cached){ setModuleCards(cached); return; }
    try{
      const j = await fetchJson(`/api/marvelcdb/module/${encodeURIComponent(name)}`);
      setModuleCards(j);
      const ms = JSON.parse(localStorage.getItem('modules')||'{}'); ms[name]=j; localStorage.setItem('modules', JSON.stringify(ms));
    }catch(e){ alert('Failed: '+e.message); }
  }

  async function fetchDeck(id){
    if(!id) return;
    if(decksCache[id]){ setMyDeck(decksCache[id]); return; }
    try{
      const j = await fetchJson(`/api/marvelcdb/deck/${id}`);
      setDecksCache(Object.assign({}, decksCache, { [id]: j }));
      setMyDeck(j);
    }catch(e){ alert('Failed to fetch deck: '+e.message); }
  }

  return e('div', {className:'card'},
    e('div', {className:'header'}, e('h2', null, `Room ${room}`), e('div', {className:'small'}, `You: ${me && me.name}`)),
    e('div', {className:'lobby'},
      e('div', {className:'column card'},
        e('h3', null, 'Players'),
        lobby ? e('ul',{className:'player-list'}, lobby.players.map(p=> e('li', {key:p.id}, `${p.name} ${p.ready? '✅':''}`))) : 'Loading...',
        e('div',{style:{marginTop:8}},
          isHost ? e('div', null,
            e('h4', null, 'Host controls'),
            e('label', null, 'Encounter module name'),
            e('input',{value:moduleName,onChange:e=>setModuleName(e.target.value)}),
            e('div',{className:'controls'},
              e('button',{onClick:()=>fetchModule(moduleName)}, 'Load Module'),
              e('button',{onClick:async ()=>{ await fetchJson(`/api/lobby/${room}/set_encounter`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({module:moduleName}) }); try{ if(typeof socket !== 'undefined' && socket) socket.emit('join_lobby', { room }); }catch(e){} alert('Set'); }}, 'Set on lobby')
            )
          ) : null
        )
      ),
      e('div', {className:'column card'},
        e('h3', null, 'Choose your deck'),
        e('label', null, 'Deck ID (from MarvelCDB)'), e('input',{value:deckId,onChange:e=>setDeckId(e.target.value)}),
        e('div',{className:'controls'}, e('button',{onClick:()=>fetchDeck(deckId)}, 'Load Deck')),
        myDeck? e(DeckPreview, {deck: myDeck}) : e('div',{className:'small'}, 'No deck loaded')
      ),
      e('div', {className:'column card'},
        e('h3', null, 'Lobby Actions'),
        e('div',{className:'controls'}, e('button',{onClick: async ()=>{
          // join API to register player
          const p = await fetchJson(`/api/lobby/${room}/join`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({name: me.name, deck_id: deckId}) });
          setMe(p);
          try{ if(typeof socket !== 'undefined' && socket) socket.emit('join_lobby', { room }); }catch(e){}
          alert('Joined as '+p.name);
        }}, 'Register to lobby')),
        e('div',{style:{marginTop:8}}, e('button',{onClick: async ()=>{
          // toggle ready
          await fetchJson(`/api/lobby/${room}/player/${me.id}/ready`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ready:true}) });
          try{ if(typeof socket !== 'undefined' && socket) socket.emit('join_lobby', { room }); }catch(e){}
          alert('Ready');
        }}, 'Mark Ready')),
  isHost? e('div',{style:{marginTop:8}}, e('button',{onClick: async ()=>{ try{ await fetchJson(`/api/lobby/${room}/start`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({host: lobby && lobby.host}) }); try{ if(typeof socket !== 'undefined' && socket) socket.emit('join_lobby', { room }); }catch(e){} onStart(); }catch(e){ alert('Failed to start: '+e.message); } }}, 'Start Game')) : null
      )
    )
  );
}

function DeckPreview({deck}){
  if(!deck) return null;
  // show a simple representation similar to MarvelCDB: name and card list
  const title = deck.name || (deck.ID? `Deck ${deck.ID}`:'Deck');
  const cardlist = deck.cards || deck.cards_in_deck || [];
  return e('div', {className:'card'}, e('h4', null, title), e('div',{className:'small'}, `Cards: ${cardlist.length}`), e('div',{style:{maxHeight:240,overflow:'auto'}}, cardlist.slice(0,200).map((c,i)=> e('div',{key:i, className:'small'}, `${c.quantity||c.q||1}x ${c.name||c.cardname||c}`))));
}

function GameView({ lobby, me, decksCache }){
  const [players, setPlayers] = useState(lobby? lobby.players : []);
  const [encounter, setEncounter] = useState([]);
  const [modalDeck, setModalDeck] = useState(null);
  
  // Find the current player (me)
  const myPlayer = players.find(p => p.id === (me && me.id)) || players[0];
  const otherPlayers = players.filter(p => p.id !== (me && me.id));

  useEffect(()=>{ if(lobby && lobby.encounter_module) loadEncounter(lobby.encounter_module); }, [lobby]);

  async function loadEncounter(moduleName){
    // check localStorage
    const ms = JSON.parse(localStorage.getItem('modules')||'{}');
    if(ms[moduleName]){ setEncounter(ms[moduleName]); return; }
    try{ const j = await fetchJson(`/api/marvelcdb/module/${encodeURIComponent(moduleName)}`); setEncounter(j); const m2=Object.assign({}, ms); m2[moduleName]=j; localStorage.setItem('modules', JSON.stringify(m2)); }catch(e){ alert('Failed to load encounter: '+e.message); }
  }

  function onDraw(playerIndex){
    const p = players[playerIndex];
    if(!p) return;
    const copy = players.slice();
    if(!copy[playerIndex].zone.deck || copy[playerIndex].zone.deck.length===0) return alert('No cards to draw');
    const top = copy[playerIndex].zone.deck.shift();
    copy[playerIndex].zone.hand.push(top);
    setPlayers(copy);
  }

  function openDeck(playerIndex){
    const p = players[playerIndex];
    if(!p) return;
    setModalDeck({ playerIndex, zone: 'deck', cards: p.zone.deck });
  }

  function moveCard(fromPlayer, fromZone, toPlayer, toZone, cardIndex){
    const copy = players.slice();
    const item = copy[fromPlayer].zone[fromZone].splice(cardIndex,1)[0];
    copy[toPlayer].zone[toZone].push(item);
    setPlayers(copy);
  }

  // Slay the Spire style layout: maximize play space, compact hand bar at bottom
  const myPlayerIdx = players.indexOf(myPlayer);
  return e('div', {className:'game-container'},
    e('div', {className:'game-area'},
      e('div', {className:'header-bar'}, e('h2', null, 'Game Board')),
      
      // Encounter zone - large and prominent
      e('div',{className:'encounter-section'},
        e('h3', null, 'Encounter'), 
        e('div', {className:'zone encounter-cards large-zone'}, 
          encounter.length === 0 ? e('div', {className:'small'}, 'No encounter cards') :
          encounter.map((c,i)=> e('div',{key:i, className:'card-tile large-card', draggable:true, onDragStart: ev => { ev.dataTransfer.setData('text/plain', JSON.stringify({fromPlayer:-1, fromZone:'encounter', index:i})); }}, 
            c.card_name || c.name || c.title || 'Card'
          ))
        )
      ),
      
      // Other players - large play areas
      e('div',{className:'other-players'},
        otherPlayers.length === 0 ? e('div', {className:'small'}, 'No other players') :
        otherPlayers.map((p, pIdx)=> e('div',{key:p.id, className:'player-board'}, 
          e('h4', null, p.name), 
          e('div', {className:'player-areas'},
            // Play area - large
            e('div', {className:'play-zone'},
              e('div',{className:'small'}, 'Play Area'), 
              e('div',{className:'zone play-cards large-zone', onDragOver: ev => ev.preventDefault(), onDrop: ev => { try{ const d = JSON.parse(ev.dataTransfer.getData('text/plain')); moveCard(d.fromPlayer, d.fromZone, otherPlayers.indexOf(p)+1, 'play', d.index); }catch(e){console.log(e)} }}, 
                p.zone.play.length === 0 ? e('div', {className:'small drop-zone'}, 'Drop here') : p.zone.play.map((c,ci)=> e('div',{key:ci, className:'card-tile large-card', draggable:true, onDragStart: ev => { ev.dataTransfer.setData('text/plain', JSON.stringify({fromPlayer:otherPlayers.indexOf(p)+1, fromZone:'play', index:ci})); }}, c.card_name||c.name||'Card'))
              )
            ),
            // Deck, discard info
            e('div', {className:'player-meta'},
              e('div', {className:'deck-info'},
                e('div',{className:'small'}, 'Deck'),
                e('div',{className:'deck-stack', onClick:()=>onDraw(otherPlayers.indexOf(p)+1), title:'Click to draw'}, `${p.zone.deck.length}`),
                e('div',{className:'controls'}, e('button',{onClick:()=>openDeck(otherPlayers.indexOf(p)+1)}, 'Open'))
              ),
              e('div', {className:'discard-zone'},
                e('div',{className:'small'}, 'Discard'), 
                e('div',{className:'zone', onDragOver: ev => ev.preventDefault(), onDrop: ev => { try{ const d = JSON.parse(ev.dataTransfer.getData('text/plain')); moveCard(d.fromPlayer, d.fromZone, otherPlayers.indexOf(p)+1, 'discard', d.index); }catch(e){} }}, 
                  p.zone.discard.length === 0 ? e('div', {className:'small drop-zone'}, 'Drop') : p.zone.discard.map((c,ci)=> e('div',{key:ci, className:'card-tile', draggable:true, onDragStart: ev => { ev.dataTransfer.setData('text/plain', JSON.stringify({fromPlayer:otherPlayers.indexOf(p)+1, fromZone:'discard', index:ci})); }}, c.card_name||c.name||'Card'))
                )
              )
            )
          )
        ))
      )
    ),
    
    // Player hand at bottom - compact bar
    myPlayer? e('div', {className:'hand-bar'},
      e('div', {className:'hand-info'},
        e('div', {className:'deck-info'},
          e('div',{className:'small'}, 'Deck'),
          e('div',{className:'deck-stack compact', onClick:()=>onDraw(myPlayerIdx), title:'Click to draw'}, `${myPlayer.zone.deck.length}`),
          e('div',{className:'controls'}, e('button',{onClick:()=>openDeck(myPlayerIdx)}, 'Open'))
        ),
        e('div', {className:'discard-info'},
          e('div',{className:'small'}, 'Discard'),
          e('div',{className:'zone compact', onDragOver: ev => ev.preventDefault(), onDrop: ev => { try{ const d = JSON.parse(ev.dataTransfer.getData('text/plain')); moveCard(d.fromPlayer, d.fromZone, myPlayerIdx, 'discard', d.index); }catch(e){} }},
            myPlayer.zone.discard.length === 0 ? e('div', {className:'small'}, '0') : e('div', {className:'small'}, `${myPlayer.zone.discard.length}`)
          )
        ),
        e('div', {className:'play-info'},
          e('div',{className:'small'}, 'Play'),
          e('div',{className:'zone compact', onDragOver: ev => ev.preventDefault(), onDrop: ev => { try{ const d = JSON.parse(ev.dataTransfer.getData('text/plain')); moveCard(d.fromPlayer, d.fromZone, myPlayerIdx, 'play', d.index); }catch(e){} }},
            myPlayer.zone.play.length === 0 ? e('div', {className:'small'}, '0') : myPlayer.zone.play.map((c,ci)=> e('div',{key:ci, className:'card-tile tiny', draggable:true, onDragStart: ev => { ev.dataTransfer.setData('text/plain', JSON.stringify({fromPlayer:myPlayerIdx, fromZone:'play', index:ci})); }}, c.card_name||c.name||'C'))
          )
        )
      ),
      e('div', {className:'hand-cards'},
        myPlayer.zone.hand.length === 0 ? e('div', {className:'small'}, 'No cards in hand') :
        myPlayer.zone.hand.map((c,ci)=> e('div',{key:ci, className:'hand-card', draggable:true, onDragStart: ev => { ev.dataTransfer.setData('text/plain', JSON.stringify({fromPlayer:myPlayerIdx, fromZone:'hand', index:ci})); }}, 
          e('div', {className:'card-name'}, c.card_name||c.name||c.title||'Card'),
          e('div', {className:'hand-card-controls'},
            e('button',{onClick: ()=>moveCard(myPlayerIdx, 'hand', myPlayerIdx, 'play', ci), title:'Play'}, 'Play'),
            e('button',{onClick: ()=>moveCard(myPlayerIdx, 'hand', myPlayerIdx, 'discard', ci), title:'Discard'}, 'Discard')
          )
        ))
      )
    ) : null,
    
    modalDeck? e(ModalDeck, {modalDeck, onClose: ()=>setModalDeck(null)}) : null
  );
}

function ModalDeck({ modalDeck, onClose }){
  return e('div', {className:'modal'}, e('div',{className:'card'}, e('h3', null, 'Deck contents'), e('div',{style:{maxHeight:480, overflow:'auto'}}, modalDeck.cards.map((c,i)=> e('div',{key:i, className:'small'}, c.card_name||c.name||c.title||'Card'))), e('div',{className:'controls'}, e('button',{onClick:onClose}, 'Close'))))
}

// Mount
const root = document.getElementById('root');
ReactDOM.createRoot(root).render(e(App));
})();
