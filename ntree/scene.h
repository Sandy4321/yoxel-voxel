#pragma once

#include "ntree/nodes.h"
#include "BrickManager.h"

class Scene
{
public:
  Scene();
  ~Scene();

  void SetTreeDepth(int depth) { m_treeDepth = depth; }
  int GetTreeDepth() const { return m_treeDepth; }

  void Load(const char * filename);
  void Save(const char * filename);

  ntree::NodePtr GetRoot() { return m_root; }

  void AddVolume(cg::point_3i pos, cg::point_3i size, const ntree::ValueType * data);

  std::string GetStats();

  ntree::ValueType TraceRay(const point_3f & p, point_3f dir);
  
private:
  ntree::NodePtr m_root;
  int m_treeDepth;

  BrickPool<uchar4> m_dataPool;
  BrickPool<uint4> m_nodePool;



};
