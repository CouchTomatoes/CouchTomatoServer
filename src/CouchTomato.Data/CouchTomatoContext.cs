using Microsoft.EntityFrameworkCore;

namespace CouchTomato.Data;

public class CouchTomatoContext : DbContext
{
    public CouchTomatoContext(DbContextOptions<CouchTomatoContext> options)
        : base(options) { }

    protected override void OnConfiguring(DbContextOptionsBuilder optionsBuilder)
        {
            if (!optionsBuilder.IsConfigured)
            {
                optionsBuilder.UseSqlite("Data Source=data/couchtomato.db");
            }
        }

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        // We’ll add entities in the next phase (Movie, Provider, etc.)
    }

    // public DbSet<Movie> Movies => Set<Movie>();  // add in later phases
}
