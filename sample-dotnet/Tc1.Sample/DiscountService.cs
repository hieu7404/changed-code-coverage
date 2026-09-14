namespace Tc1.Sample;

/// <summary>A deterministic sample policy; amounts are returned without rounding.</summary>
public sealed class DiscountService
{
    public decimal CalculateTotal(decimal subtotal)
    {
        if (subtotal < 0m)
        {
            throw new ArgumentOutOfRangeException(nameof(subtotal));
        }

        if (subtotal >= 1000m)
        {
            // Intentionally not exercised by WP0 tests; verify with coverage in WP1.
            return subtotal * 0.80m;
        }

        if (subtotal >= 100m)
        {
            return subtotal * 0.90m;
        }

        return subtotal;
    }
}