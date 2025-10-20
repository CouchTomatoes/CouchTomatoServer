using Microsoft.EntityFrameworkCore;
using CouchTomato.Data.Entities;

namespace CouchTomato.Data;

public class CouchTomatoContext : DbContext
{
    public CouchTomatoContext(DbContextOptions<CouchTomatoContext> options)
        : base(options) { }

    public DbSet<Movie> Movies => Set<Movie>(); 

    protected override void OnConfiguring(DbContextOptionsBuilder optionsBuilder)
        {
            if (!optionsBuilder.IsConfigured)
            {
                optionsBuilder.UseSqlite("Data Source=data/couchtomato.db");
            }
        }

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        // Apply configurations for all entity types
        modelBuilder.ApplyConfigurationsFromAssembly(typeof(CouchTomatoContext).Assembly);
            
        modelBuilder.Entity<Movie>().HasData(
            new Movie
            {
                KeyID = long.Parse("1"),
                Title = "The Shawshank Redemption",
                Year = 1994,
                CreatedDate = DateTime.UtcNow,
                ModifiedDate = DateTime.UtcNow,
                IsDeleted = false
            },
            new Movie
            {
                KeyID =  long.Parse("2"),
                Title = "The Godfather",
                Year = 1972,
                CreatedDate = DateTime.UtcNow,
                ModifiedDate = DateTime.UtcNow,
                IsDeleted = false
            }
        );
    }
}
