using Tc1.Sample;

namespace Tc1.Sample.Tests;

public sealed class DiscountServiceTests
{
    private readonly DiscountService service = new();

    [Theory]
    [InlineData(0, 0)]
    [InlineData(99, 99)]
    [InlineData(100, 90)]
    [InlineData(250, 225)]
    public void CalculateTotal_ReturnsExpectedTotal(int subtotal, int expected)
    {
        Assert.Equal((decimal)expected, service.CalculateTotal(subtotal));
    }

    [Fact]
    public void CalculateTotal_BelowBulkThreshold_PreservesFractionalAmount()
    {
        Assert.Equal(899.10m, service.CalculateTotal(999m));
    }

    [Theory]
    [InlineData(-1)]
    [InlineData(-100)]
    public void CalculateTotal_NegativeSubtotal_RejectsInput(int subtotal)
    {
        var error = Assert.Throws<ArgumentOutOfRangeException>(
            () => service.CalculateTotal(subtotal));

        Assert.Equal("subtotal", error.ParamName);
    }
}