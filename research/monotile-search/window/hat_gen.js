const cos=Math.cos, sin=Math.sin, PI=Math.PI;
const r3 = 1.7320508075688772;
const hr3 = 0.8660254037844386;
const ident = [1, 0, 0, 0, 1, 0];

function pt( x, y )
{
	return { x : x, y : y };
}

function hexPt( x, y )
{
	return pt( x + 0.5*y, hr3*y );
}

// Affine matrix inverse
function inv( T ) {
	const det = T[0]*T[4] - T[1]*T[3];
	return [T[4]/det, -T[1]/det, (T[1]*T[5]-T[2]*T[4])/det,
		-T[3]/det, T[0]/det, (T[2]*T[3]-T[0]*T[5])/det];
};

// Affine matrix multiply
function mul( A, B )
{
	return [A[0]*B[0] + A[1]*B[3], 
		A[0]*B[1] + A[1]*B[4],
		A[0]*B[2] + A[1]*B[5] + A[2],

		A[3]*B[0] + A[4]*B[3], 
		A[3]*B[1] + A[4]*B[4],
		A[3]*B[2] + A[4]*B[5] + A[5]];
}

function padd( p, q )
{
	return { x : p.x + q.x, y : p.y + q.y };
}

function psub( p, q )
{
	return { x : p.x - q.x, y : p.y - q.y };
}

// Rotation matrix
function trot( ang )
{
	const c = cos( ang );
	const s = sin( ang );
	return [c, -s, 0, s, c, 0];
}

// Translation matrix
function ttrans( tx, ty )
{
	return [1, 0, tx, 0, 1, ty];
}

function rotAbout( p, ang )
{
	return mul( ttrans( p.x, p.y ), 
		mul( trot( ang ), ttrans( -p.x, -p.y ) ) );
}

// Matrix * point
function transPt( M, P )
{
	return pt(M[0]*P.x + M[1]*P.y + M[2], M[3]*P.x + M[4]*P.y + M[5]);
}

// Match unit interval to line segment p->q
function matchSeg( p, q )
{
	return [q.x-p.x, p.y-q.y, p.x,  q.y-p.y, q.x-p.x, p.y];
};

// Match line segment p1->q1 to line segment p2->q2
function matchTwo( p1, q1, p2, q2 )
{
	return mul( matchSeg( p2, q2 ), inv( matchSeg( p1, q1 ) ) );
};

// Intersect two lines defined by segments p1->q1 and p2->q2
function intersect( p1, q1, p2, q2 )
{
    const d = (q2.y - p2.y) * (q1.x - p1.x) - (q2.x - p2.x) * (q1.y - p1.y);
    const uA = ((q2.x - p2.x) * (p1.y - p2.y) - (q2.y - p2.y) * (p1.x - p2.x)) / d;
    // const uB = ((q1.x - p1.x) * (p1.y - p2.y) - (q1.y - p1.y) * (p1.x - p2.x)) / d;

    return pt( p1.x + uA * (q1.x - p1.x), p1.y + uA * (q1.y - p1.y) );
}

const hat_outline = [
    hexPt(0, 0), hexPt(-1,-1), hexPt(0,-2), hexPt(2,-2),
    hexPt(2,-1), hexPt(4,-2), hexPt(5,-1), hexPt(4, 0),
    hexPt(3, 0), hexPt(2, 2), hexPt(0, 3), hexPt(0, 2),
    hexPt(-1, 2) ];
class HatTile
{
	constructor( label )
	{
		this.label = label;
		this.svg_id = null;
	}

	draw( S, level )
	{
		drawPolygon( 
			hat_outline, S, cols[this.label].color(), black, 1 );
	}

	resetSVG()
	{
		this.svg_id = null;
	}

	buildSVGDefs( stream, sc )
	{
		if( this.svg_id != null ) {
			return;
		}

		this.svg_id = getSVGID();
		stream.push( polygonToSVG( hat_outline, this.svg_id, 
			cols[this.label].color(), black, lw_scale/sc ) );
	}

	getSVGStrokeID()
	{
		return null;
	}

	getSVGFillID()
	{
		return this.svg_id;
	}

	getText( stream, T )
	{
		// Write out the top two rows of an affine transformation matrix
		// giving the location of this hat, together with the type of 
		// this tile.
		stream.push( `${this.label} ${T[0]} ${T[1]} ${T[2]} ${T[3]} ${T[4]} ${T[5]}` )
	}
}

// A group that collects a list of transformed children and an outline
class MetaTile
{
	constructor( shape, width )
	{
		this.shape = shape;
		this.width = width;
		this.children = [];
		this.svg_id = null;
	}

	addChild( T, geom )
	{
		this.children.push( { T : T, geom : geom } );
	}

	evalChild( n, i )
	{
		return transPt( this.children[n].T, this.children[n].geom.shape[i] );
	}

	draw( S, level )
	{
		if( level > 0 ) {
			for( let g of this.children ) {
				g.geom.draw( mul( S, g.T ), level - 1 );
			}
		} else {
			drawPolygon( this.shape, S, null, black, this.width );
		}
	}

	recentre()
	{
		let cx = 0;
		let cy = 0;
		for( let p of this.shape ) {
			cx += p.x;
			cy += p.y;
		}
		cx /= this.shape.length;
		cy /= this.shape.length;
		const tr = pt( -cx, -cy );

		for( let idx = 0; idx < this.shape.length; ++idx ) {
			this.shape[idx] = padd( this.shape[idx], tr );
		}

		const M = ttrans( -cx, -cy );
		for( let ch of this.children ) {
			ch.T = mul( M, ch.T );
		}
	}

	resetSVG()
	{
		for( let ch of this.children ) {
			ch.geom.resetSVG();
		}
		this.svg_id = null;
	}

	buildSVGDefs( stream, sc )
	{
		if( this.svg_id != null ) {
			return;
		}

		this.svg_id = getSVGID();

		for( let ch of this.children ) {
			ch.geom.buildSVGDefs( stream, sc );
		}

		// Construct a fill group that must live at a logical lowest
		// layer in the draw order.

		stream.push( `  <g id="${this.getSVGFillID()}">` );
		for( let ch of this.children ) {
			const fid = ch.geom.getSVGFillID();
			if( fid != null ) {
				stream.push( getSVGInstance( fid, ch.T ) );
			}
		}
		stream.push( '  </g>' );

		// Construct a stroke group that must live above all fill groups.

		stream.push( `  <g id="${this.getSVGStrokeID()}">` );
		for( let ch of this.children ) {
			const sid = ch.geom.getSVGStrokeID();
			if( sid != null ) {
				stream.push( getSVGInstance( sid, ch.T ) );
			}
		}
		stream.push( polygonToSVG( this.shape, 
			null, null, black, this.width*lw_scale/sc ) );

		stream.push( '  </g>' );
	}

	getSVGStrokeID()
	{
		return `${this.svg_id}s`;
	}

	getSVGFillID()
	{
		return `${this.svg_id}f`;
	}

	getText( stream, T )
	{
		for( let g of this.children ) {
			g.geom.getText( stream, mul( T, g.T ) );
		}
	}
}

const H1_hat = new HatTile( 'H1' );
const H_hat = new HatTile( 'H' );
const T_hat = new HatTile( 'T' );
const P_hat = new HatTile( 'P' );
const F_hat = new HatTile( 'F' );

const H_init = (function () {
	const H_outline = [
		pt( 0, 0 ), pt( 4, 0 ), pt( 4.5, hr3 ),
		pt( 2.5, 5 * hr3 ), pt( 1.5, 5 * hr3 ), pt( -0.5, hr3 ) ];
	const meta = new MetaTile( H_outline, 2 );

	meta.addChild( 
		matchTwo( 
			hat_outline[5], hat_outline[7], H_outline[5], H_outline[0] ),
		H_hat );
	meta.addChild( 
		matchTwo( 
			hat_outline[9], hat_outline[11], H_outline[1], H_outline[2] ),
		H_hat );
	meta.addChild( 
		matchTwo( 
			hat_outline[5], hat_outline[7], H_outline[3], H_outline[4] ),
		H_hat );
	meta.addChild( 
		mul( ttrans( 2.5, hr3 ), 
			mul( 
				[-0.5,-hr3,0,hr3,-0.5,0],
				[0.5,0,0,0,-0.5,0] ) ),
		H1_hat );

	return meta; }());

const T_init = (function () {
	const T_outline = [
		pt( 0, 0 ), pt( 3, 0 ), pt( 1.5, 3 * hr3 ) ];
	const meta = new MetaTile( T_outline, 2 );

	meta.addChild( 
		[0.5, 0, 0.5, 0, 0.5, hr3],
		T_hat );

	return meta; }());

const P_init = (function () {
	const P_outline = [
		pt( 0, 0 ), pt( 4, 0 ), 
		pt( 3, 2 * hr3 ), pt( -1, 2 * hr3 ) ];
	const meta = new MetaTile( P_outline, 2 );

	meta.addChild( 
		[0.5, 0, 1.5, 0, 0.5, hr3],
		P_hat );
	meta.addChild( 
		mul( ttrans( 0, 2 * hr3 ), 
			mul( [0.5, hr3, 0, -hr3, 0.5, 0],
				 [0.5, 0.0, 0.0, 0.0, 0.5, 0.0] ) ),
		P_hat );

	return meta; }());

const F_init = (function () {
	const F_outline = [
		pt( 0, 0 ), pt( 3, 0 ), 
		pt( 3.5, hr3 ), pt( 3, 2 * hr3 ), pt( -1, 2 * hr3 ) ];
	const meta = new MetaTile( F_outline, 2 );

	meta.addChild( 
		[0.5, 0, 1.5, 0, 0.5, hr3],
		F_hat );
	meta.addChild( 
		mul( ttrans( 0, 2 * hr3 ), 
			mul( [0.5, hr3, 0, -hr3, 0.5, 0],
				 [0.5, 0.0, 0.0, 0.0, 0.5, 0.0] ) ),
		F_hat );

	return meta; }());

function constructPatch( H, T, P, F )
{
	const rules = [
		['H'],
		[0, 0, 'P', 2],
		[1, 0, 'H', 2],
		[2, 0, 'P', 2],
		[3, 0, 'H', 2],
		[4, 4, 'P', 2],
		[0, 4, 'F', 3],
		[2, 4, 'F', 3],
		[4, 1, 3, 2, 'F', 0],
		[8, 3, 'H', 0],
		[9, 2, 'P', 0],
		[10, 2, 'H', 0],
		[11, 4, 'P', 2],
		[12, 0, 'H', 2],
		[13, 0, 'F', 3],
		[14, 2, 'F', 1],
		[15, 3, 'H', 4],
		[8, 2, 'F', 1], 
		[17, 3, 'H', 0],
		[18, 2, 'P', 0],
		[19, 2, 'H', 2],
		[20, 4, 'F', 3],
		[20, 0, 'P', 2],
		[22, 0, 'H', 2],
		[23, 4, 'F', 3],
		[23, 0, 'F', 3],
		[16, 0, 'P', 2],
		[9, 4, 0, 2, 'T', 2],
		[4, 0, 'F', 3] 
		];

	ret = new MetaTile( [], H.width );
	shapes = { 'H' : H, 'T' : T, 'P' : P, 'F' : F };

	for( let r of rules ) {
		if( r.length == 1 ) {
			ret.addChild( ident, shapes[r[0]] );
		} else if( r.length == 4 ) {
			const poly = ret.children[r[0]].geom.shape;
			const T = ret.children[r[0]].T;
			const P = transPt( T, poly[(r[1]+1)%poly.length] );
			const Q = transPt( T, poly[r[1]] );
			const nshp = shapes[r[2]];
			const npoly = nshp.shape;

			ret.addChild(
				matchTwo( npoly[r[3]], npoly[(r[3]+1)%npoly.length], P, Q ),
				nshp );
		} else {
			const chP = ret.children[r[0]];
			const chQ = ret.children[r[2]];

			const P = transPt( chQ.T, chQ.geom.shape[r[3]] );
			const Q = transPt( chP.T, chP.geom.shape[r[1]] );
			const nshp = shapes[r[4]];
			const npoly = nshp.shape;

			ret.addChild(
				matchTwo( npoly[r[5]], npoly[(r[5]+1)%npoly.length], P, Q ),
				nshp );
		}
	}

	return ret;
}

function constructMetatiles( patch )
{
	const bps1 = patch.evalChild( 8, 2 );
	const bps2 = patch.evalChild( 21, 2 );
	const rbps = transPt( rotAbout( bps1, -2.0*PI/3.0 ), bps2 );

	const p72 = patch.evalChild( 7, 2 );
	const p252 = patch.evalChild( 25, 2 );

	const llc = intersect( bps1, rbps,
		patch.evalChild( 6, 2 ), p72 );
	let w = psub( patch.evalChild( 6, 2 ), llc );

	const new_H_outline = [llc, bps1];
	w = transPt( trot( -PI/3 ), w );
	new_H_outline.push( padd( new_H_outline[1], w ) );
	new_H_outline.push( patch.evalChild( 14, 2 ) );
	w = transPt( trot( -PI/3 ), w );
	new_H_outline.push( psub( new_H_outline[3], w ) );
	new_H_outline.push( patch.evalChild( 6, 2 ) );

	const new_H = new MetaTile( new_H_outline, patch.width * 2 );
	for( let ch of [0, 9, 16, 27, 26, 6, 1, 8, 10, 15] ) {
		new_H.addChild( patch.children[ch].T, patch.children[ch].geom );
	}

	const new_P_outline = [ p72, padd( p72, psub( bps1, llc ) ), bps1, llc ];
	const new_P = new MetaTile( new_P_outline, patch.width * 2 );
	for( let ch of [7,2,3,4,28] ) {
		new_P.addChild( patch.children[ch].T, patch.children[ch].geom );
	}

	const new_F_outline = [ 
		bps2, patch.evalChild( 24, 2 ), patch.evalChild( 25, 0 ),
		p252, padd( p252, psub( llc, bps1 ) ) ];
	const new_F = new MetaTile( new_F_outline, patch.width * 2 );
	for( let ch of [21,20,22,23,24,25] ) {
		new_F.addChild( patch.children[ch].T, patch.children[ch].geom );
	}
	
	const AAA = new_H_outline[2];
	const BBB = padd( new_H_outline[1], 
		psub( new_H_outline[4], new_H_outline[5] ) );
	const CCC = transPt( rotAbout( BBB, -PI/3 ), AAA );
	const new_T_outline = [BBB,CCC,AAA];
	const new_T = new MetaTile( new_T_outline, patch.width * 2 );
	new_T.addChild( patch.children[11].T, patch.children[11].geom );

	new_H.recentre();
	new_P.recentre();
	new_F.recentre();
	new_T.recentre();

	return [new_H, new_T, new_P, new_F]
}
const N=parseInt(process.argv[2]||'5');
let tiles=[H_init,T_init,P_init,F_init]; tag(tiles);
for(let i=0;i<N;i++){ const patch=constructPatch(...tiles); tiles=constructMetatiles(patch); tag(tiles);}
const out=[]; let mid=0; const meta=[];  // meta: [id, level, type, angle, parent]
function flat(g,T,lev,parent,type){
  if(g instanceof HatTile){ out.push([g.label,...T,parent]); return; }
  const id=mid++; meta.push([id,lev,type,Math.round(Math.atan2(T[3],T[0])*180/Math.PI+360)%360,parent]);
  const types=['H','T','P','F'];
  for(const c of g.children){ const ct = (c.geom instanceof HatTile)?null: c.geom.__type; flat(c.geom, mul(T,c.T), lev-1, id, ct); }
}
// tag metatile objects with their type at every level
function tag(ts){ ['H','T','P','F'].forEach((n,i)=>ts[i].__type=n); }

flat(tiles[0], ident, N, -1, 'H');
require('fs').writeFileSync('meta_L'+N+'.json', JSON.stringify(meta));
require('fs').writeFileSync('hats_L'+N+'.json', JSON.stringify(out));
console.log('hats',out.length);
