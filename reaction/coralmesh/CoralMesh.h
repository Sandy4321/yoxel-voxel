struct edge_t
{
  int a, b;
  edge_t() : a(-1), b(-1) {}
  edge_t(int a_, int b_) : a(a_), b(b_) {}
  edge_t flip() const { return edge_t(b, a); }
  bool valid() const { return a >= 0 && b >=0 && a != b; }
  operator size_t() const { return (a<<16) + b; }
};

struct face_t
{
  int a, b, c;
  face_t() : a(0), b(0), c(0) {}
  face_t(int a_, int b_, int c_) : a(a_), b(b_), c(c_) {}
};

inline bool operator< (const edge_t & e1, const edge_t & e2) 
{
  if (e1.a != e2.a)
    return e1.a < e2.a;
  else
    return e1.b < e2.b;
}

inline bool operator== (const edge_t & e1, const edge_t & e2) 
{
  return e1.a == e2.a && e1.b == e2.b;
}

inline bool operator!= (const edge_t & e1, const edge_t & e2) 
{
  return !(e1==e2);
}


class CoralMesh
{
public:
  CoralMesh();

  int AddVert(const point_3f & p);
  int AddFace(int a, int b, int c);

  int GetVertNum() const { return m_pos.size(); }
  int GetFaceNum() const { return m_faces.size(); }
  const point_3f* GetPositions() const { return &m_pos[0]; }
  const point_3f* GetNormals() const { return &m_normal[0]; }
  const face_t*   GetFaces() const { return &m_faces[0]; }
  
  void UpdateNormals();
  void Grow(float mergeDist, float splitDist, const float * amounts);
private:
  std::vector<point_3f>    m_pos;
  std::vector<point_3f>    m_normal;
  std::vector<face_t>      m_faces;

  struct EdgeData
  {
    int face;
    edge_t next;
    EdgeData() : face(-1) {}
    EdgeData(int face_, const edge_t & next_) : face(face_), next(next_) {}
  };
  typedef stdext::hash_map<edge_t, EdgeData> EDGE_MAP;
  typedef EDGE_MAP::const_iterator EDGE_ITER;
  EDGE_MAP m_edges;

  int m_totalMergeCount;

  void setFace(int fid, int a, int b, int c);
  float edgeLen2(const edge_t & e);
  void splitEdge(const edge_t & e);
  point_3f interpolateVertex(int a, int b, point_3f & n);
  void splitEdgeFace(const edge_t & e, int vid);
  void shrinkEdge(const edge_t & e);
  void removeFace(int fid);

  void getAdjacentVerts(const edge_t & edre, std::vector<int> & res);
};