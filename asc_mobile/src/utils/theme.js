import { useColorScheme } from 'react-native';

const LIGHT = {
  g900:'#0D1F1A', g800:'#1B4332', g700:'#2D6A4F', g600:'#40916C',
  g300:'#74C69D', g200:'#B7E4C7', g100:'#D8F3DC', g50:'#F0FAF4',
  amber:'#D97706', amberBg:'#FEF3C7', amberDk:'#92400E',
  red:'#DC2626',   redBg:'#FEF2F2',   redDk:'#991B1B',
  blue:'#2563EB',  blueBg:'#EFF6FF',  blueDk:'#1E3A8A',
  ink:'#111827', ink2:'#374151', ink3:'#6B7280', ink4:'#D1D5DB',
  surf:'#F9FAFB', card:'#FFFFFF',
  brd:'rgba(0,0,0,.09)', brd2:'rgba(0,0,0,.06)',
  primary:'#1B4332', primaryLight:'#2D6A4F', primaryPale:'#D8F3DC',
  white:'#FFFFFF', bg:'#F9FAFB',
  success:'#40916C', warning:'#D97706', danger:'#DC2626', info:'#2563EB',
};
const DARK = {
  g900:'#D8F3DC', g800:'#74C69D', g700:'#52B788', g600:'#40916C',
  g300:'#2D6A4F', g200:'#1B4332', g100:'#143327', g50:'#0D1F1A',
  amber:'#FCD34D', amberBg:'#1C1500', amberDk:'#FDE68A',
  red:'#F87171', redBg:'#1A0A0A', redDk:'#FCA5A5',
  blue:'#60A5FA', blueBg:'#0A0F1A', blueDk:'#93C5FD',
  ink:'#F9FAFB', ink2:'#E5E7EB', ink3:'#9CA3AF', ink4:'#4B5563',
  surf:'#0F1117', card:'#1A1D27',
  brd:'rgba(255,255,255,.1)', brd2:'rgba(255,255,255,.06)',
  primary:'#52B788', primaryLight:'#74C69D', primaryPale:'#0D1F1A',
  white:'#111827', bg:'#0F1117',
  success:'#52B788', warning:'#FCD34D', danger:'#F87171', info:'#60A5FA',
};

export function useTheme() {
  const scheme = useColorScheme();
  return scheme === 'dark' ? DARK : LIGHT;
}

export const COLORS = LIGHT;
export const RADIUS = { sm:8, md:12, lg:16, xl:20, pill:99 };
export const SHADOW = {
  sm: { shadowColor:'#000', shadowOffset:{width:0,height:1}, shadowOpacity:.05, shadowRadius:3, elevation:2 },
  md: { shadowColor:'#000', shadowOffset:{width:0,height:2}, shadowOpacity:.07, shadowRadius:8, elevation:4 },
  lg: { shadowColor:'#000', shadowOffset:{width:0,height:4}, shadowOpacity:.09, shadowRadius:16, elevation:6 },
};
export const STATUS = {
  pending:   { bg:'#FEF3C7', text:'#92400E', label:'Pending'   },
  in_review: { bg:'#EFF6FF', text:'#1E3A8A', label:'In Review' },
  approved:  { bg:'#D8F3DC', text:'#2D6A4F', label:'Approved'  },
  rejected:  { bg:'#FEF2F2', text:'#991B1B', label:'Rejected'  },
  returned:  { bg:'#FEF3C7', text:'#92400E', label:'Returned'  },
  completed: { bg:'#F0FAF4', text:'#40916C', label:'Completed' },
};
export const PRIORITY_COLOR = {
  low:'#9CA3AF', normal:'#2563EB', high:'#D97706', urgent:'#DC2626',
};
