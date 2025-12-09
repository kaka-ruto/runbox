require "minitest/autorun"

def add(a, b)
  a + b
end

class TestMath < Minitest::Test
  def test_add
    assert_equal 5, add(2, 3)
  end
end

