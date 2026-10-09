export const ROUTES={shop:{label:'فروشگاه',brand:'NOOR HOME',features:['cart','delivery']},restaurant:{label:'رستوران',brand:'SAFFRON TABLE',features:['booking','menu']}};
export const STYLES=['modern','warm'];
export function initial(){return{step:'welcome',route:null,style:'warm',features:[]};}
export function chooseRoute(state,route){if(!ROUTES[route])throw new Error('Unknown route');return{...state,route,step:'style',features:state.route===route?[...state.features]:[]};}
export function chooseStyle(state,style){if(!state.route||!STYLES.includes(style))throw new Error('Invalid style');return{...state,style,step:'features'};}
export function toggleFeature(state,key){if(state.step!=='features'||!ROUTES[state.route]?.features.includes(key))throw new Error('Invalid feature');return{...state,features:state.features.includes(key)?state.features.filter(v=>v!==key):[...state.features,key]};}
export function back(state){const previous={summary:'features',features:'style',style:'business',business:'business',welcome:'business'};return{...state,step:previous[state.step],features:[...state.features]};}
export function finalize(state){if(state.step!=='features'||!state.route)throw new Error('Invalid transition');return{...state,step:'summary',features:[...state.features]};}
