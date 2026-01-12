(function(){
const e = React.createElement;
const { useState } = React;

// generate sample card objects
function makeCard(i, prefix='P'){ return { id: `${prefix}${i}`, name: `${prefix} Card ${i}`, image: null } }

const SAMPLE_PLAYER_DECK = Array.from({length:20}, (_,i)=> makeCard(i+1,'P'));
const SAMPLE_ENCOUNTER_DECK = Array.from({length:20}, (_,i)=> makeCard(i+1,'E'));

function TestApp(){
  const [playerZone, setPlayerZone] = useState({ deck: [...SAMPLE_PLAYER_DECK], hand: [], discard: [], play: [] });
  const [encounter, setEncounter] = useState([...SAMPLE_ENCOUNTER_DECK]);
  const [modal, setModal] = useState(null);

  function draw(){
    if(playerZone.deck.length===0) return alert('Deck empty');
    const copy = { ...playerZone, deck: [...playerZone.deck], hand: [...playerZone.hand] };
    const card = copy.deck.shift();
    copy.hand.push(card);
    setPlayerZone(copy);
  }

  function openDeck(){ setModal({title:'Player Deck', cards: playerZone.deck}); }
  function openEncounter(){ setModal({title:'Encounter Deck', cards: encounter}); }

  function playFromHand(index){ const copy = {...playerZone, hand:[...playerZone.hand], play:[...playerZone.play]}; const c = copy.hand.splice(index,1)[0]; copy.play.push(c); setPlayerZone(copy); }
  function discardFromHand(index){ const copy = {...playerZone, hand:[...playerZone.hand], discard:[...playerZone.discard]}; const c = copy.hand.splice(index,1)[0]; copy.discard.push(c); setPlayerZone(copy); }

  const children = [];
  children.push(e('h2', {key:'h2'}, 'UI Test - No server'));
  children.push(
    e('div', {key:'board', className:'board'},
      e('div',{className:'card column', style:{flex:2}}, e('h3', null, 'Encounter'), e('div',{className:'zone'}, encounter.slice(0,8).map((c,i)=> e('div',{key:c.id,className:'card-tile'}, e('div', null, c.name))))),
      e('div',{className:'column', style:{flex:3}},
        e('div',{className:'card'}, e('h4', null, 'Player'), e('div',{className:'flex'},
          e('div',{className:'column'}, e('div',{className:'small'}, 'Deck'), e('div',{className:'deck-stack', onClick:draw}, `${playerZone.deck.length}`), e('div',{className:'controls'}, e('button',{onClick:openDeck}, 'Open'))),
          e('div',{className:'column'}, e('div',{className:'small'}, 'Hand'), e('div',{className:'hand'}, playerZone.hand.length === 0 ? e('div', {className:'small'}, 'No cards') : playerZone.hand.map((c,ci)=> e('div',{key:c.id,className:'card-tile'}, e('div',null,c.name), e('div',null, e('button',{onClick:()=>playFromHand(ci)}, 'Play'), e('button',{onClick:()=>discardFromHand(ci)}, 'Discard')))))),
          e('div',{className:'column'}, e('div',{className:'small'}, 'Discard'), e('div',{className:'zone'}, playerZone.discard.length === 0 ? e('div', {className:'small'}, 'Empty') : playerZone.discard.map((c,i)=> e('div',{key:c.id,className:'card-tile'}, e('div',null,c.name))))),
          e('div',{className:'column'}, e('div',{className:'small'}, 'Play Area'), e('div',{className:'zone'}, playerZone.play.length === 0 ? e('div', {className:'small'}, 'Empty') : playerZone.play.map((c,i)=> e('div',{key:c.id,className:'card-tile'}, e('div',null,c.name)))))
        ))
      )
    )
  );

  if(modal){
    children.push(e('div',{key:'modal', className:'modal'}, e('div',{className:'card'}, e('h3', null, modal.title), e('div',{style:{maxHeight:420,overflow:'auto'}}, modal.cards.map((c,i)=> e('div',{key:c.id,className:'small'}, `${c.name}`))), e('div',{className:'controls'}, e('button',{onClick:()=>setModal(null)}, 'Close')))));
  }

  return e('div', {className:'card'}, ...children);
}

const root = document.getElementById('root');
ReactDOM.createRoot(root).render(e(TestApp));
})();
